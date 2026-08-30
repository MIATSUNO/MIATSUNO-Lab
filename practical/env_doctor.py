"""Inspect the local runtime and selected network endpoints."""

import argparse
import json
import os
import platform
import shutil
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path


def inspect_path(value):
    path = Path(value).expanduser()
    exists = path.exists()
    result = {"path": str(path), "exists": exists}
    if exists:
        result.update(
            {
                "type": "directory" if path.is_dir() else "file" if path.is_file() else "other",
                "readable": os.access(path, os.R_OK),
                "writable": os.access(path, os.W_OK),
            }
        )
    return result


def inspect_url(url, timeout):
    request = urllib.request.Request(url, headers={"User-Agent": "env-doctor/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"url": url, "ok": True, "status": response.status, "content_type": response.headers.get_content_type()}
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        status = getattr(exc, "code", None)
        return {"url": url, "ok": False, "status": status, "error": str(exc)}


def collect(args):
    executables = {name: shutil.which(name) for name in args.executable}
    result = {
        "python": {"version": platform.python_version(), "executable": sys.executable},
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "working_directory": str(Path.cwd()),
        "executables": executables,
        "paths": [inspect_path(value) for value in args.path],
        "environment": {name: bool(os.environ.get(name)) for name in args.environment},
    }
    if args.url:
        result["network"] = inspect_url(args.url, args.timeout)
    return result


def passed(result):
    executable_ok = all(value is not None for value in result["executables"].values())
    paths_ok = all(item["exists"] and item.get("readable", False) for item in result["paths"])
    env_ok = all(result["environment"].values())
    network_ok = result.get("network", {}).get("ok", True)
    return executable_ok and paths_ok and env_ok and network_ok


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check local runtime prerequisites and optional network access.")
    parser.add_argument("--executable", action="append", default=["python3"], help="Executable that must be discoverable; repeatable.")
    parser.add_argument("--path", action="append", default=[], help="Path that must exist and be readable; repeatable.")
    parser.add_argument("--environment", action="append", default=[], help="Environment variable that must be set; repeatable.")
    parser.add_argument("--url", help="URL to request with a real HTTP GET.")
    parser.add_argument("--timeout", type=float, default=8.0, help="Network timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)
    result = collect(args)
    result["ok"] = passed(result)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"environment: {'ok' if result['ok'] else 'issues found'}")
        print(f"python: {result['python']['version']} ({result['python']['executable']})")
        for name, value in result["executables"].items():
            print(f"executable {name}: {value or 'missing'}")
        for item in result["paths"]:
            print(f"path {item['path']}: {'ok' if item['exists'] and item.get('readable', False) else 'unavailable'}")
        for name, present in result["environment"].items():
            print(f"environment variable {name}: {'set' if present else 'missing'}")
        if "network" in result:
            network = result["network"]
            print(f"network {network['url']}: {'ok' if network['ok'] else network.get('error', 'failed')}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

