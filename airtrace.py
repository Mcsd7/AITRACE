
import csv
import json
import os
import re
import socket
import subprocess
import time
import urllib.request
from datetime import datetime
from collections import deque

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text

console = Console()
historico = deque(maxlen=45)
ARQUIVO_CSV = "airtrace_historico.csv"

ultimo_ping = {"latencia": None, "perda": None, "erro": "Aguardando"}
ultimo_dns = "Aguardando"
ultima_internet = "Aguardando"
ultima_verificacao = 0
ultima_api = 0
info_atual = {}


def wifi_info():
    try:
        r = subprocess.run(
            ["termux-wifi-connectioninfo"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            return json.loads(r.stdout)
        return {"erro": r.stderr.strip() or "API indisponivel"}
    except Exception as e:
        return {"erro": str(e)}


def salvar_csv(info, ping, dns, internet):
    novo = not os.path.exists(ARQUIVO_CSV)
    try:
        with open(ARQUIVO_CSV, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if novo:
                w.writerow([
                    "data_hora", "ip", "rssi_dbm", "frequencia_mhz",
                    "link_mbps", "ping_ms", "perda_pct", "dns", "internet"
                ])
            w.writerow([
                datetime.now().isoformat(timespec="seconds"),
                info.get("ip", ""),
                info.get("rssi", ""),
                info.get("frequency_mhz", ""),
                info.get("link_speed_mbps", ""),
                ping.get("latencia") if ping.get("latencia") is not None else "",
                ping.get("perda") if ping.get("perda") is not None else "",
                dns, internet
            ])
    except OSError:
        pass


def testar_ping():
    try:
        r = subprocess.run(
            ["ping", "-c", "1", "-W", "2", "1.1.1.1"],
            capture_output=True, text=True, timeout=4
        )
        saida = r.stdout + r.stderr

        m = re.search(r"time[=<]([\d.]+)\s*ms", saida)
        p = re.search(r"(\d+(?:\.\d+)?)%\s*packet loss", saida)

        latencia = float(m.group(1)) if m else None
        perda = float(p.group(1)) if p else (0.0 if latencia is not None else 100.0)

        return {
            "latencia": latencia,
            "perda": perda,
            "erro": "OK" if latencia is not None else "Sem resposta"
        }
    except Exception as e:
        return {"latencia": None, "perda": None, "erro": str(e)}


def testar_dns():
    try:
        inicio = time.monotonic()
        socket.getaddrinfo("example.com", 443, type=socket.SOCK_STREAM)
        ms = (time.monotonic() - inicio) * 1000
        return f"OK ({ms:.0f} ms)"
    except Exception:
        return "FALHOU"


def testar_internet():
    try:
        req = urllib.request.Request(
            "https://connectivitycheck.gstatic.com/generate_204",
            headers={"User-Agent": "AIRTRACE/2.1"}
        )
        inicio = time.monotonic()
        with urllib.request.urlopen(req, timeout=4) as resp:
            ms = (time.monotonic() - inicio) * 1000
            if resp.status == 204:
                return f"ONLINE ({ms:.0f} ms)"
            return f"HTTP {resp.status}"
    except Exception:
        return "SEM ACESSO"


def canal_wifi(freq):
    if not isinstance(freq, (int, float)) or freq <= 0:
        return "N/D"
    if 2412 <= freq <= 2472:
        return str(round((freq - 2407) / 5))
    if freq == 2484:
        return "14"
    if 5000 <= freq < 5900:
        return str(round((freq - 5000) / 5))
    if 5955 <= freq <= 7115:
        return str(round((freq - 5950) / 5))
    return "N/D"


def barra_sinal(rssi):
    if not isinstance(rssi, (int, float)) or rssi >= 0:
        return "[dim]Sinal indisponivel[/]"

    if rssi >= -50:
        cor, qualidade = "bright_green", "Excelente"
    elif rssi >= -60:
        cor, qualidade = "green", "Muito bom"
    elif rssi >= -67:
        cor, qualidade = "yellow", "Bom"
    elif rssi >= -75:
        cor, qualidade = "dark_orange", "Fraco"
    else:
        cor, qualidade = "red", "Muito fraco"

    n = max(0, min(20, round((rssi + 100) / 70 * 20)))
    barra = f"[{cor}]" + "█" * n + "[/]"
    barra += "[dim]" + "░" * (20 - n) + "[/]"
    return f"{barra}\n[{cor}]{rssi} dBm | {qualidade}[/]"


def grafico():
    if not historico:
        return "[dim]Aguardando leituras...[/]"
    chars = "▁▂▃▄▅▆▇█"
    resultado = ""
    for v in historico:
        i = max(0, min(7, int((v + 100) / 70 * 7)))
        resultado += f"[green]{chars[i]}[/]"
    return resultado


def valor_ping():
    ms = ultimo_ping.get("latencia")
    if ms is not None:
        return f"{ms:.1f} ms"
    return ultimo_ping.get("erro", "N/D")


def montar_painel(info):
    freq = info.get("frequency_mhz", 0)
    rssi = info.get("rssi")
    velocidade = info.get("link_speed_mbps", 0)
    conectado = info.get("supplicant_state") == "COMPLETED"

    cabecalho = Text()
    cabecalho.append("  AIRTRACE ", style="bold bright_green")
    cabecalho.append("2.1\n", style="bold cyan")
    cabecalho.append(
        "  WIFI MONITOR  //  ANDROID + TERMUX:API",
        style="dim cyan"
    )

    antena = Text()
    antena.append("          .\n", style="bright_green")
    antena.append("         / \\\n", style="bright_green")
    antena.append("        /   \\\n", style="green")
    antena.append("       /  ", style="green")
    antena.append("●", style="bold bright_green")
    antena.append("  \\\n", style="green")
    antena.append("      /_____\\\n", style="green")
    antena.append("          |\n", style="cyan")
    antena.append("          |\n", style="cyan")
    antena.append("       ___|___\n", style="bright_green")
    antena.append("      /_______\\\n", style="bright_green")
    antena.append("\n  PASSIVE MODE", style="bold cyan")

    tabela = Table(box=box.SIMPLE, expand=True, show_header=False)
    tabela.add_column("Campo", style="cyan")
    tabela.add_column("Valor", style="bright_white")

    tabela.add_row(
        "Estado",
        "[bright_green]CONECTADO[/]" if conectado else "[red]DESCONECTADO[/]"
    )
    tabela.add_row("IP local", str(info.get("ip", "N/D")))
    tabela.add_row("SSID", str(info.get("ssid", "N/D")))
    tabela.add_row("Frequencia", f"{freq} MHz" if freq else "N/D")
    tabela.add_row("Canal", canal_wifi(freq))
    tabela.add_row("Link Wi-Fi", f"{velocidade} Mbps")
    tabela.add_row(
        "RSSI",
        f"{rssi} dBm" if isinstance(rssi, (int, float)) else "N/D"
    )
    tabela.add_row("Ping", valor_ping())
    tabela.add_row("Perda", (
        f"{ultimo_ping['perda']:.0f}%"
        if ultimo_ping.get("perda") is not None else "N/D"
    ))
    tabela.add_row("DNS", ultimo_dns)
    tabela.add_row("Internet", ultima_internet)

    painel_dados = Panel(
        tabela,
        title="[bold cyan]NETWORK DIAGNOSTICS[/]",
        border_style="cyan"
    )
    painel_antena = Panel(
        antena,
        title="[bold green]AIRTRACE[/]",
        border_style="green"
    )
    painel_sinal = Panel(
        f"{barra_sinal(rssi)}\n\n"
        "[dim]HISTORICO DO SINAL (dBm)[/]\n"
        f"{grafico()}",
        title="[bold green]SIGNAL ANALYSIS[/]",
        border_style="green"
    )
    rodape = Panel(
        f"[green]●[/] Monitoramento ativo  "
        f"[dim]|[/] {datetime.now():%H:%M:%S}\n"
        f"[dim]CSV: {ARQUIVO_CSV} | CTRL+C para sair[/]",
        border_style="dim"
    )

    layout = Layout()
    layout.split_column(
        Layout(Panel(cabecalho, border_style="bright_green"), size=4),
        Layout(name="principal", ratio=3),
        Layout(painel_sinal, size=7),
        Layout(rodape, size=3)
    )
    layout["principal"].split_row(
        Layout(painel_antena, ratio=1),
        Layout(painel_dados, ratio=2)
    )
    return layout


def main():
    global ultimo_ping, ultimo_dns, ultima_internet
    global ultima_verificacao, ultima_api, info_atual

    console.clear()

    try:
        with Live(console=console, refresh_per_second=4, screen=True) as live:
            while True:
                agora = time.monotonic()

                # Atualiza os dados do Wi-Fi a cada 4 segundos.
                if agora - ultima_api >= 4:
                    info_atual = wifi_info()
                    rssi = info_atual.get("rssi")
                    if isinstance(rssi, (int, float)) and rssi < 0:
                        historico.append(rssi)
                    ultima_api = agora

                # Testes de rede a cada 15 segundos.
                if agora - ultima_verificacao >= 15:
                    ultimo_ping = testar_ping()
                    ultimo_dns = testar_dns()
                    ultima_internet = testar_internet()
                    salvar_csv(
                        info_atual, ultimo_ping,
                        ultimo_dns, ultima_internet
                    )
                    ultima_verificacao = time.monotonic()

                live.update(montar_painel(info_atual))
                time.sleep(1)

    except KeyboardInterrupt:
        console.print("\n[bold red]AIRTRACE encerrado.[/]")
        console.print(f"Historico salvo em: {ARQUIVO_CSV}")


if __name__ == "__main__":
    main()
