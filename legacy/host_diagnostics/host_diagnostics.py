#!/usr/bin/env python3
import argparse
import socket
import sys
import time


def parse_ports(value):
    try:
        ports = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise argparse.ArgumentTypeError("ports must be comma-separated numbers") from error
    if not ports or len(ports) > 8 or any(port < 1 or port > 65535 for port in ports):
        raise argparse.ArgumentTypeError("provide 1 to 8 ports between 1 and 65535")
    return list(dict.fromkeys(ports))


def resolve(host):
    records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    addresses = []
    for family, _, _, _, sockaddr in records:
        address = sockaddr[0]
        item = (family, address)
        if item not in addresses:
            addresses.append(item)
    return addresses


def check_port(addresses, port, timeout):
    attempts = []
    for family, address in addresses:
        started = time.perf_counter()
        connection = socket.socket(family, socket.SOCK_STREAM)
        connection.settimeout(timeout)
        try:
            result = connection.connect_ex((address, port))
            elapsed = (time.perf_counter() - started) * 1000
            attempts.append((result == 0, address, elapsed, result))
        except OSError as error:
            elapsed = (time.perf_counter() - started) * 1000
            attempts.append((False, address, elapsed, str(error)))
        finally:
            connection.close()
    return attempts


def build_parser():
    parser = argparse.ArgumentParser(description="Resolve and diagnose one host without scanning a network.")
    parser.add_argument("host", help="one hostname or IP address")
    parser.add_argument("--ports", type=parse_ports, default=[80, 443], help="comma-separated TCP ports, up to 8 (default: 80,443)")
    parser.add_argument("--timeout", type=float, default=2.0, help="seconds per TCP connection attempt (default: 2.0)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.timeout <= 0 or args.timeout > 30:
        parser.error("--timeout must be greater than 0 and no more than 30")
    try:
        addresses = resolve(args.host)
    except socket.gaierror as error:
        print("DNS resolution failed:", error, file=sys.stderr)
        return 1
    print("Host:", args.host)
    print("Resolved addresses:")
    for _, address in addresses:
        try:
            name = socket.gethostbyaddr(address)[0]
        except (socket.herror, socket.gaierror):
            name = "no reverse name"
        print("-", address, "(", name, ")")
    print("TCP checks:")
    for port in args.ports:
        attempts = check_port(addresses, port, args.timeout)
        for open_state, address, elapsed, detail in attempts:
            state = "open" if open_state else "closed or filtered"
            print(f"- {address}:{port} {state}; {elapsed:.1f} ms; detail={detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

