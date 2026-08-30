import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_url(value):
    value = value.strip()
    parts = urlsplit(value)
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError(f"Invalid URL: {value}")
    netloc = parts.hostname.lower()
    if parts.port is not None:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, ""))


def load_state(path):
    if not path.exists():
        return {"version": 1, "sites": {}}
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read state file {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("sites"), dict):
        raise ValueError("State file has an invalid format.")
    value.setdefault("version", 1)
    return value


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def parse_headers(values):
    headers = {}
    forbidden = {"host", "content-length", "connection", "transfer-encoding"}
    for value in values:
        if ":" not in value:
            raise ValueError(f"Header must use NAME:VALUE format: {value}")
        name, content = value.split(":", 1)
        name = name.strip()
        content = content.strip()
        if not name or not content:
            raise ValueError(f"Header must contain a name and value: {value}")
        if name.lower() in forbidden:
            raise ValueError(f"Header is not allowed: {name}")
        headers[name] = content
    return headers


def response_body(response, maximum):
    declared = response.headers.get("Content-Length")
    if declared:
        try:
            if int(declared) > maximum:
                raise ValueError(f"Response exceeded the {maximum} byte limit.")
        except ValueError as exc:
            if str(exc).startswith("Response exceeded"):
                raise
    body = response.read(maximum + 1)
    if len(body) > maximum:
        raise ValueError(f"Response exceeded the {maximum} byte limit.")
    return body


def fetch(url, previous, args, headers):
    request_headers = {"User-Agent": args.user_agent, "Accept": "*/*"}
    request_headers.update(headers)
    if previous:
        if previous.get("etag"):
            request_headers["If-None-Match"] = str(previous["etag"])
        if previous.get("last_modified"):
            request_headers["If-Modified-Since"] = str(previous["last_modified"])
    request = Request(url, headers=request_headers, method="GET")
    checked_at = now()
    try:
        with urlopen(request, timeout=args.timeout) as response:
            status = int(response.status)
            body = response_body(response, args.max_bytes)
            current = {
                "url": url,
                "status_code": status,
                "final_url": canonical_url(response.geturl()),
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
                "checked_at": checked_at,
                "error": None,
            }
    except HTTPError as exc:
        if exc.code == 304 and previous:
            current = dict(previous)
            current["checked_at"] = checked_at
            current["status_code"] = 304
            current["error"] = None
            return {"url": url, "result": "unchanged", "state": current, "status_code": 304}
        return {"url": url, "status": "error", "status_code": getattr(exc, "code", None), "checked_at": checked_at, "error": f"HTTP error {exc.code}: {exc.reason}"}
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return {"url": url, "status": "error", "checked_at": checked_at, "error": f"Request failed: {exc}"}
    if not previous:
        result = "new"
    elif any(current.get(key) != previous.get(key) for key in ("sha256", "status_code", "final_url")):
        result = "changed"
    else:
        result = "unchanged"
    return {"url": url, "result": result, "state": current, "status_code": current["status_code"]}


def read_urls(args):
    values = list(args.urls)
    if args.url_file:
        try:
            with Path(args.url_file).expanduser().open("r", encoding="utf-8") as handle:
                values.extend(line.strip() for line in handle if line.strip() and not line.lstrip().startswith("#"))
        except OSError as exc:
            raise ValueError(f"Unable to read URL file: {exc}") from exc
    unique = []
    seen = set()
    for value in values:
        url = canonical_url(value)
        if url not in seen:
            unique.append(url)
            seen.add(url)
    if not unique:
        raise ValueError("Provide at least one URL or a non-empty --url-file.")
    return unique


def output_results(results, as_json):
    if as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return
    for result in results:
        if result.get("result"):
            status = result.get("status_code", "?")
            print(f"{result['result'].upper():9} {status!s:4} {result['url']}")
        else:
            status = result.get("status_code", "error")
            print(f"ERROR     {status!s:4} {result['url']}: {result['error']}", file=sys.stderr)


def run(args):
    try:
        urls = read_urls(args)
        headers = parse_headers(args.header)
        state_path = Path(args.state).expanduser().resolve()
        state = load_state(state_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    changed_seen = False
    error_seen = False
    while True:
        results = []
        for url in urls:
            previous = state["sites"].get(url)
            result = fetch(url, previous, args, headers)
            if result.get("result"):
                state["sites"][url] = result["state"]
                changed_seen = changed_seen or result["result"] in {"new", "changed"}
            else:
                error_seen = True
                retained = dict(previous or {})
                retained.update({"url": url, "checked_at": result["checked_at"], "error": result["error"]})
                if result.get("status_code") is not None:
                    retained["status_code"] = result["status_code"]
                state["sites"][url] = retained
            results.append({key: value for key, value in result.items() if key != "state"})
        try:
            state["updated_at"] = now()
            save_state(state_path, state)
        except OSError as exc:
            print(f"Unable to save state: {exc}", file=sys.stderr)
            return 1
        output_results(results, args.json)
        if args.interval <= 0:
            break
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("Stopped.", file=sys.stderr)
            break
    if error_seen:
        return 1
    if args.fail_on_change and changed_seen:
        return 3
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="site_watch", description="Monitor HTTP(S) URLs and persist SHA-256 fingerprints for change detection.")
    parser.add_argument("urls", nargs="*", help="HTTP or HTTPS URL(s) to monitor")
    parser.add_argument("-f", "--url-file", help="Text file containing one URL per line")
    parser.add_argument("-s", "--state", default=".site_watch_state.json", help="JSON state path (default: .site_watch_state.json)")
    parser.add_argument("-i", "--interval", type=float, default=0, help="Seconds between checks; repeat until interrupted when positive")
    parser.add_argument("-t", "--timeout", type=float, default=20, help="Per-request timeout in seconds (default: 20)")
    parser.add_argument("--max-bytes", type=int, default=5 * 1024 * 1024, help="Maximum response size to hash (default: 5242880)")
    parser.add_argument("--user-agent", default="site_watch/1.0", help="HTTP User-Agent value")
    parser.add_argument("--header", action="append", default=[], help="Additional request header in NAME:VALUE form; may be repeated")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON results")
    parser.add_argument("--fail-on-change", action="store_true", help="Exit with status 3 when a URL is new or changed")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.interval < 0 or args.timeout <= 0 or args.max_bytes <= 0:
        parser.error("--interval must be non-negative; --timeout and --max-bytes must be positive")
    try:
        return run(args)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
