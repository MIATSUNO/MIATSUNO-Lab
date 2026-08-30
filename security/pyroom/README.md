# pyroom

`pyroom` is a read-only HTTP reconnaissance checklist for a target you own or are explicitly allowed to test. It runs named probes and prints JSON, covering status, headers, common documents, CORS signals, methods, and other defensive observations. Despite the playful name, it is deliberately not an exploit tool.

## Prerequisites and installation

You need Python 3 and `requests`:

```bash
python3 --version
python3 -m pip install requests
```

Or use an isolated environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install requests
```

## Basic commands

The command-line interface is:

```text
usage: security/pyroom.py [-h] [--checks CHECKS] [--timeout TIMEOUT]
                                [--list]
                                [url]
```

List the available check names before selecting any:

```bash
python3 security/pyroom.py --list
```

Run every check against an authorized endpoint, or choose a comma-separated subset:

```bash
python3 security/pyroom.py https://example.com
python3 security/pyroom.py https://example.com --checks check_http_status,check_security_headers --timeout 5
```

The flags are `--checks`, `--timeout`, and `--list`; `url` is optional only when `--list` is used. The `--list` output contains 45 check names, from `check_http_status` and `check_security_headers` through `check_hsts_preload`, `check_xss_protection`, and `check_vary_header`.

## Input and output

A target may be written with or without a scheme; missing schemes become `https://`. Each selected check makes a request (mostly `GET`; `check_options` and `check_http_methods` use `OPTIONS`). CORS/origin checks send the constant probe origin `https://security.invalid`. The JSON result contains the normalized `url`, a `checks` array, and `passed`/`total` counts. Each check reports `ok`, status/final URL when available, and a compact `details` object.

A small selection returns JSON shaped like:

```json
{
  "url": "https://example.com",
  "checks": [
    {"check": "check_http_status", "ok": true, "status": 200, "final_url": "https://example.com/", "details": {"redirects": 0, "https": true}}
  ],
  "passed": 1,
  "total": 1
}
```

A request error is kept as a check with `ok: false` and an `error`; unknown check names or invalid timeouts are rejected by argparse.

## Network and safety notes

Only run it against systems you are authorized to assess. It performs real HTTP requests and may request common paths such as `/robots.txt`, `/.well-known/security.txt`, `/health`, `/openapi.json`, `/manifest.json`, and `/favicon.ico`; it also sends `OPTIONS` for method checks and a harmless synthetic Origin for CORS checks. It does not submit forms, exploit vulnerabilities, brute-force, or write data. The default timeout is 10 seconds, and full runs can generate many requests. Responses include headers and body data internally, so do not point it at sensitive systems casually.

## Troubleshooting

- **`a target URL is required`:** provide a URL unless you only want `--list`.
- **`unknown checks`:** copy names exactly from `python3 security/pyroom.py --list`, separated by commas.
- **Timeouts or many failed checks:** reduce the scope with `--checks`, increase `--timeout` carefully, and verify the target is reachable.
- **`requests` import error:** install it in the active virtual environment.
