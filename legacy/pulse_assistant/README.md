# pulse_assistant

A small command-line assistant that performs two real lookups: current weather from Open-Meteo and English definitions from Dictionary API. It has no account, API key, database, or local service to run.

## Installation

Requires Python 3.9 or newer and an internet connection. From this directory:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 pulse_assistant.py --help
```

The program uses only Python's standard library.

## Usage

The exact command help is:

```text
usage: pulse_assistant.py [-h] {weather,define} ...

A small local assistant backed by public web APIs.

positional arguments:
  {weather,define}
    weather       show current weather for a place
    define        look up an English dictionary entry

options:
  -h, --help      show this help message and exit
```

Subcommand help is available with `python3 pulse_assistant.py weather --help` and `python3 pulse_assistant.py define --help`.

## Examples

```bash
python3 pulse_assistant.py weather "São Paulo"
python3 pulse_assistant.py define resilient
```

## Audience

People learning Python HTTP requests, users who want quick terminal lookups, and anyone who prefers a tiny local interface over a browser tab.

## Limitations

Weather is current data returned by Open-Meteo and is not a forecast or emergency service. Location matching selects the first geocoding result. Definitions are English-only and depend on Dictionary API availability. Network failures, rate limits, and a disconnected network produce an error instead of invented data.

## Safety notes

Only the place or word entered is sent to the named public service. Do not enter private addresses, secrets, or sensitive text. Review the services' terms and privacy policies before regular use.

