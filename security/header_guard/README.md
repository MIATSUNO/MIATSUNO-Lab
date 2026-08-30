# header_guard

`header_guard` is a quick defensive check for a web endpoint's HTTP security headers. It follows redirects, reports what is missing or weak, and returns a failing status when the response is not healthy enough for the check.

## Prerequisites and installation

You need Python 3 and the `requests` package:

```bash
python3 --version
python3 -m pip install requests
```

A virtual environment is a good idea if this is part of a larger project:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install requests
```

## Basic command

The actual interface is:

```text
usage: security/header_guard.py [-h] [--timeout TIMEOUT] [--json] url
```

Run the human-readable check, or ask for machine-readable JSON:

```bash
python3 security/header_guard.py https://example.com
python3 security/header_guard.py example.com --timeout 5 --json
```

The flags are the help-listed `--timeout` and `--json`; the positional `url` must be HTTP or HTTPS. A bare hostname is normalized to `https://`.

## Input and output

The script performs a real `GET` with a small identifying User-Agent and follows redirects. It checks for `strict-transport-security`, `content-security-policy`, `x-content-type-options`, `referrer-policy`, and `permissions-policy`. It also requires either `x-frame-options` or a `frame-ancestors` directive, and marks HSTS without `max-age=` as weak.

For a response that lacks policies, text output has this shape:

```text
URL: https://example.com
Status: 200
Final URL: https://example.com/
Missing: content-security-policy, permissions-policy
Weak: none
```

The normal exit code is 0 only when the request succeeds and there are no missing or weak findings. Connection errors print `Error: ...` and return 1; invalid URLs are reported by argparse. `--json` includes the original URL, final URL, status, HTTPS/redirect information, response headers, `missing`, and `weak`.

## Network and safety notes

Use this only on URLs you are authorized to inspect. It is a read-only `GET`: it does not exploit, mutate, log in, or change server configuration. Redirects mean the request may reach another host, so inspect `Final URL` before trusting the result. The default timeout is 10 seconds. JSON output includes all response headers, which can contain operational details; avoid pasting it into public logs.

## Troubleshooting

- **Missing `requests`:** install it in the same Python environment used to run the script.
- **Bare hostname fails:** try an explicit `https://` URL and verify DNS/TLS connectivity.
- **A known-good site exits 1:** this tool is intentionally strict; “missing” or “weak” is a finding, not a Python crash.
- **Unexpected redirect:** check `Final URL`; the tool follows redirects by design.
