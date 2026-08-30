# env_doctor

`env_doctor` gives a quick, JSON-friendly snapshot of the local runtime and a few explicitly requested checks. It reports Python/platform details, executable locations, path readability, whether environment variables are set, and (optionally) one real HTTP GET.

## Prerequisites and installation

Python 3 is all it needs; every import is from the standard library:

```bash
python3 --version
```

There is no dependency file or package installation. Run it from the checkout with `python3 practical/env_doctor.py`.

## Basic command

The script's actual help is:

```text
usage: practical/env_doctor.py [-h] [--executable EXECUTABLE] [--path PATH]
                               [--environment ENVIRONMENT] [--url URL]
                               [--timeout TIMEOUT] [--json]
```

A plain check looks for `python3` (the default), while extra checks can be repeated:

```bash
python3 practical/env_doctor.py
python3 practical/env_doctor.py --executable git --path . --environment HOME --json
python3 practical/env_doctor.py --url https://example.com --timeout 5
```

The flags copied from help are repeatable `--executable`, `--path`, and `--environment`, plus `--url`, `--timeout`, and `--json`.

## Input and output

`--executable` uses `shutil.which`; `--path` expands `~` and checks existence/readability; `--environment` checks presence (not the value). `--url` performs a real HTTP GET with User-Agent `env-doctor/1.0`. No URL means no network check.

Text output looks like:

```text
environment: ok
python: 3.x.y (/usr/bin/python3)
executable python3: /usr/bin/python3
path .: ok
environment variable HOME: set
network https://example.com: ok
```

`--json` prints an object with `python`, `platform`, `working_directory`, `executables`, `paths`, `environment`, optional `network`, and `ok`. Exit status is 0 only when all requested checks pass; otherwise it is 1.

## Network and safety notes

The local checks are read-only. If `--url` is supplied, the tool sends one GET to that URL and follows the normal URL opener behavior; use an endpoint you are allowed to contact. The URL response body is not printed or saved—only status/content type or an error is retained. The script has no external API requirement.

## Troubleshooting

- **`executable ...: missing`:** install the tool or check that the right virtual environment/PATH is active.
- **`path ...: unavailable`:** verify the spelling, permissions, and `~` expansion.
- **Environment variable missing:** export it in the same shell that runs the command.
- **Network failed:** test DNS/proxy/TLS separately, or omit `--url` when you only need local diagnostics.
- **Unexpected failure status:** `ok` is an aggregate; inspect each printed line or JSON field to find the failing check.
