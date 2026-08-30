# host_diagnostics

A focused network diagnostic for one hostname or IP address. It resolves that host, attempts reverse DNS, and checks only the explicitly listed TCP ports with bounded timeouts.

## Installation

Requires Python 3.9 or newer and a network-enabled environment. It uses only the standard library.

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 host_diagnostics.py --help
```

## Usage

The exact command help is:

```text
usage: host_diagnostics.py [-h] [--ports PORTS] [--timeout TIMEOUT] host

Resolve and diagnose one host without scanning a network.

positional arguments:
  host               one hostname or IP address

options:
  -h, --help         show this help message and exit
  --ports PORTS      comma-separated TCP ports, up to 8 (default: 80,443)
  --timeout TIMEOUT  seconds per TCP connection attempt (default: 2.0)
```

## Examples

```bash
python3 host_diagnostics.py example.org
python3 host_diagnostics.py router.local --ports 53,80,443 --timeout 1.5
python3 host_diagnostics.py 192.0.2.10 --ports 22
```

## Audience

People troubleshooting a host they administer, learners exploring DNS and TCP behavior, and support technicians who need a compact terminal report.

## Limitations

A successful TCP connection does not prove that an application is healthy, and a failed connection may be caused by a firewall or transient network issue. Reverse DNS is optional and may be unavailable. The program does not send ICMP, perform service fingerprinting, follow redirects, or scan ranges.

## Safety notes

Run this only against a host you own or are explicitly authorized to diagnose. It makes real DNS lookups and TCP connection attempts to one host and up to eight chosen ports. Use a conservative timeout and follow the network owner's rules.

