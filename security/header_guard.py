import argparse
import json
import sys
from urllib.parse import urlparse

import requests

TIMEOUT = 10
REQUIRED_HEADERS = {
    "strict-transport-security": "HTTPS transport policy",
    "content-security-policy": "browser execution policy",
    "x-content-type-options": "MIME sniffing protection",
    "referrer-policy": "referrer disclosure policy",
    "permissions-policy": "browser capability policy",
}


def normalize_url(value):
    candidate = value.strip()
    if not candidate:
        raise ValueError("URL is empty")
    if "://" not in candidate:
        candidate = "https://" + candidate
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must use HTTP or HTTPS and include a host")
    return candidate


def inspect_headers(url, timeout=TIMEOUT):
    target = normalize_url(url)
    try:
        response = requests.get(
            target,
            allow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "MIATSUNO-Lab-security-header-guard/1.0"},
        )
    except requests.RequestException as exc:
        return {"url": target, "ok": False, "error": str(exc), "headers": {}, "missing": list(REQUIRED_HEADERS)}
    headers = {key.lower(): value for key, value in response.headers.items()}
    missing = [name for name in REQUIRED_HEADERS if name not in headers]
    weak = []
    if response.url.startswith("https://") and "strict-transport-security" in headers:
        if "max-age=" not in headers["strict-transport-security"].lower():
            weak.append("strict-transport-security")
    if "x-frame-options" not in headers and "frame-ancestors" not in headers.get("content-security-policy", "").lower():
        missing.append("x-frame-options-or-frame-ancestors")
    return {
        "url": target,
        "final_url": response.url,
        "ok": response.ok,
        "status": response.status_code,
        "https": response.url.startswith("https://"),
        "redirects": len(response.history),
        "headers": dict(response.headers),
        "missing": sorted(set(missing)),
        "weak": weak,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect defensive HTTP security headers on an authorized URL")
    parser.add_argument("url", help="HTTP or HTTPS URL to inspect")
    parser.add_argument("--timeout", type=float, default=TIMEOUT)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        result = inspect_headers(args.url, args.timeout)
    except ValueError as exc:
        parser.error(str(exc))
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("URL:", result["url"])
        if not result["ok"]:
            print("Error:", result["error"])
            return 1
        print("Status:", result["status"])
        print("Final URL:", result["final_url"])
        print("Missing:", ", ".join(result["missing"]) or "none")
        print("Weak:", ", ".join(result["weak"]) or "none")
    return 0 if result["ok"] and not result["missing"] and not result["weak"] else 1


if __name__ == "__main__":
    sys.exit(main())

