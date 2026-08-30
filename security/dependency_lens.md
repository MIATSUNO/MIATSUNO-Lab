# dependency_lens

`dependency_lens` reads a Python requirements file, looks up each package on PyPI, and can optionally ask OSV for known vulnerabilities. It is a lightweight visibility tool, not a replacement for a lockfile audit or a complete software-supply-chain review.

## Prerequisites and installation

You need Python 3, `requests`, and a readable requirements file:

```bash
python3 --version
python3 -m pip install requests
```

For an isolated setup:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install requests
```

## Basic command

The real help is:

```text
usage: security/dependency_lens.py [-h] [--osv] [--timeout TIMEOUT] path
```

Compare a file with live PyPI metadata:

```bash
python3 security/dependency_lens.py requirements.txt
```

Include the public OSV vulnerability query as well:

```bash
python3 security/dependency_lens.py requirements.txt --osv --timeout 15
```

The flags are exactly `--osv` and `--timeout`; `path` is the requirements file.

## Input and output

The parser accepts ordinary requirement lines with a package name and an optional `==`, `~=`, `>=`, `<=`, `!=`, `>`, or `<` version. Blank lines, comments, and lines beginning with `-` are skipped. It does not claim to fully parse every pip requirements feature.

Output is indented JSON. For example, a small `requirements.txt` containing `requests==2.32.0` produces records shaped like:

```json
{
  "path": "requirements.txt",
  "requirements": [{"name": "requests", "operator": "==", "version": "2.32.0"}],
  "metadata": [{"name": "requests", "ok": true, "latest": "...", "summary": "...", "url": "..."}]
}
```

With `--osv`, an `osv` object is added with `vulnerabilities`; package lookup failures make the process return 1. A successful lookup with no OSV findings reports an empty list. Network/API failures are represented in JSON rather than silently treated as proof that a package is safe.

## Network and safety notes

Each package is requested from `https://pypi.org/pypi/<name>/json`. `--osv` additionally sends package names and versions to `https://api.osv.dev/v1/querybatch`. These are public services, so results can be unavailable, rate-limited, or change over time. The tool does not install, upgrade, or modify dependencies. Avoid putting private package indexes or secrets in the input file or captured output.

## Troubleshooting

- **`requests` import error:** install it into the active interpreter, then rerun `python3 -c 'import requests'`.
- **Every package is `ok: false`:** check internet access, DNS, proxy settings, and the package name spelling.
- **A line is missing:** this parser skips options (`-r`, `--index-url`) and comments; use simple package requirement lines for this report.
- **OSV is unavailable:** rerun without `--osv` for PyPI metadata, or try again later; an OSV failure is reported as `ok: false`.
