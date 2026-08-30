# site_watch

`site_watch` takes a fingerprint of HTTP(S) responses and remembers it. Run it again later and it tells you whether each URL is `NEW`, `UNCHANGED`, or `CHANGED`. It is handy for watching a small list of pages or endpoints without setting up a service.

## Prerequisites and installation

You need Python 3. There are no third-party packages; the script uses the standard library:

```bash
python3 --version
```

Run from the checkout as `python3 automation/site_watch.py`, or put that path in a small shell script of your own.

## Basic commands

The real `--help` shows:

```text
usage: site_watch [-h] [-f URL_FILE] [-s STATE] [-i INTERVAL] [-t TIMEOUT]
                  [--max-bytes MAX_BYTES] [--user-agent USER_AGENT]
                  [--header HEADER] [--json] [--fail-on-change]
                  [urls ...]
```

Watch one URL. The first run is `NEW` and creates `.site_watch_state.json`:

```bash
python3 automation/site_watch.py https://example.com
```

Watch several URLs and keep state somewhere explicit:

```bash
python3 automation/site_watch.py -s .watch.json https://example.com https://www.python.org/
```

For a larger list, use one URL per line (`#` lines are ignored):

```bash
python3 automation/site_watch.py --url-file urls.txt --json --fail-on-change
```

The options copied from help are `-f/--url-file`, `-s/--state`, `-i/--interval`, `-t/--timeout`, `--max-bytes`, `--user-agent`, repeatable `--header NAME:VALUE`, `--json`, and `--fail-on-change`. A positive `--interval` repeats checks until interrupted.

## Input and output

URLs are normalized to HTTP or HTTPS, lower-case the hostname, keep the path/query, and drop fragments. The tool fetches with `GET`, follows normal `urllib` redirects, hashes the response body with SHA-256, and stores status, final URL, size, ETag, Last-Modified, and check time in the state JSON. It uses conditional headers when the previous response provided validators.

A normal first/second-run text result looks like:

```text
NEW       200  https://example.com/
UNCHANGED 304  https://example.com/
```

A changed body or status is printed as `CHANGED`; request problems are printed to stderr as `ERROR`. `--json` prints a JSON array of result objects instead. `--fail-on-change` returns exit status 3 when any URL is new or changed; request errors return 1.

## Network and safety notes

This is a read-only monitor, but it does make real HTTP GET requests to every URL supplied. Only monitor endpoints you are allowed to contact. It does not execute downloaded content. The default per-request timeout is 20 seconds and the default response limit is 5,242,880 bytes; keep `--max-bytes` sensible. Custom headers can carry secrets, so do not put credentials in shell history or a committed URL list. State files may contain URLs and response metadata.

## Troubleshooting

- **“Provide at least one URL…”:** pass a URL or a non-empty `--url-file`.
- **Invalid URL/header errors:** use `https://host/path` (or a host that can be normalized) and headers exactly as `NAME:VALUE`.
- **A page is always changed:** redirects, status codes, and the response bytes are all part of the fingerprint; check the saved state and final URL.
- **Large response rejected:** raise `--max-bytes` only when you understand the memory and bandwidth cost.
- **Repeated mode will not stop:** press Ctrl-C; it prints `Stopped.` and exits the current loop.
