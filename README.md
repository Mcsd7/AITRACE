
# AITRACE 2.1

**Wi-Fi monitoring and network diagnostics for Android and Termux.**

AITRACE is a Python-based terminal tool with a neon dashboard for monitoring Wi-Fi connection details and checking network connectivity. No root required.

## Features

- Wi-Fi signal strength (RSSI)
- SSID, frequency, channel and link speed
- Ping, latency and packet loss tests
- DNS resolution test
- Internet connectivity check
- CSV history logging
- Neon terminal dashboard
- No root required

## Requirements

- Android with Termux
- Python 3
- Termux:API app and package
- Internet connection for online tests

## Installation

Update packages and install dependencies:

```bash
pkg update
pkg install python termux-api git -y
pip install rich
```

Clone the repository:

```bash
git clone https://github.com/Mcsd7/AITRACE.git
cd AITRACE
```

Run AITRACE:

```bash
python airtrace.py
```

## Notes

Some Wi-Fi information may be restricted by Android. Link speed is the negotiated Wi-Fi connection rate, not your actual internet download speed. The CSV log may contain local network information, so review it before sharing.

## Disclaimer

For educational use and network diagnostics on networks you are authorized to use.

## License

MIT License. See [LICENSE](LICENSE).
