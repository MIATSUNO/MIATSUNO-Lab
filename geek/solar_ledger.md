# solar_ledger

`solar_ledger` fetches the civil sunrise, sunset, and daylight duration for a latitude/longitude and optionally appends that record to a local JSON ledger. It is a pleasantly small way to keep real solar data instead of guessing from a calendar.

## Prerequisites and installation

You need Python 3 with its standard library:

```bash
python3 --version
```

There is no package to install. Run it as `python3 geek/solar_ledger.py`.

## Basic command

The actual help is:

```text
usage: geek/solar_ledger.py [-h] --latitude LATITUDE --longitude LONGITUDE
                            [--date DATE] [--timeout TIMEOUT] [--save SAVE]
                            [--json]
```

For example, São Paulo is approximately latitude `-23.5505`, longitude `-46.6333`:

```bash
python3 geek/solar_ledger.py --latitude -23.5505 --longitude -46.6333
python3 geek/solar_ledger.py --latitude -23.5505 --longitude -46.6333 --date 2026-08-30 --save solar.json
python3 geek/solar_ledger.py --latitude -23.5505 --longitude -46.6333 --json
```

The help-listed options are required `--latitude` and `--longitude`, plus `--date`, `--timeout`, `--save`, and `--json`. Dates must be `YYYY-MM-DD`; latitude is -90..90 and longitude is -180..180. The date defaults to today in UTC.

## Input and output

The script calls Open-Meteo's forecast endpoint with the coordinate, date, `sunrise,sunset,daylight_duration`, and `timezone=auto`. Plain output looks like:

```text
2026-08-30 at -23.5505, -46.6333 (America/Sao_Paulo)
sunrise: 2026-08-30T06:18
sunset: 2026-08-30T17:55
daylight: 11.605 hours
saved to solar.json
```

Exact times depend on the live response. `--json` prints a record with `source`, `source_url`, coordinates, date, timezone, sunrise, sunset, `daylight_seconds`, `daylight_hours`, and `retrieved_at`. `--save` appends that record to a JSON list, creating parent directories as needed.

## Network/API and safety notes

This is a read-only request to the public Open-Meteo API at `https://api.open-meteo.com/v1/forecast`; it does not need an API key and does not modify the service. Coordinates and requested dates are sent to that endpoint. The default HTTP timeout is 12 seconds. Saved data is local JSON and is rewritten as the list grows, so keep a backup if the ledger matters.

Solar times are data from the provider, not a promise about local conditions or legal/civil time decisions. Check the returned `timezone` and date if you are using the record for anything important.

## Troubleshooting

- **Argument rejected:** use decimal coordinates within the documented ranges and a real `YYYY-MM-DD` date.
- **“could not retrieve solar data”:** check internet/DNS/TLS access and try again; the service is live.
- **Ledger error:** ensure `--save` points to a writable location containing a JSON list (or a new path).
- **Unexpected timezone:** Open-Meteo chooses `timezone=auto`; inspect the JSON `timezone` field.
