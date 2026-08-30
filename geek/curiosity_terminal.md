# curiosity_terminal

`curiosity_terminal` brings a little Wikipedia wandering to the terminal. It can fetch a random article summary or search article titles/snippets in a chosen language, with an optional JSON form for scripts.

## Prerequisites and installation

You need Python 3. The script uses only the standard library, so installation is just:

```bash
python3 --version
```

Run it as `python3 geek/curiosity_terminal.py`.

## Basic commands

The real help is:

```text
usage: geek/curiosity_terminal.py [-h] [--language LANGUAGE]
                                  [--timeout TIMEOUT] [--json]
                                  {random,search} ...
```

Fetch a random English summary, search Portuguese Wikipedia, or get structured JSON:

```bash
python3 geek/curiosity_terminal.py random
python3 geek/curiosity_terminal.py --language pt search 'história do rádio' --limit 3
python3 geek/curiosity_terminal.py --language en --json search astronomy --limit 2
```

The commands copied from help are `random` (“Fetch a random article summary”) and `search` (“Search encyclopedia titles and snippets”). `search` takes `query [query ...]` and `--limit`; global options are `--language`, `--timeout`, and `--json`. Search limits must be 1–50; language is lowercase letters only.

## Input and output

The tool requests Wikimedia's live APIs. `random` calls the language wiki's `/api/rest_v1/page/random/summary`; `search` calls `/w/api.php` with the joined query and limit. Human random output prints title, optional description, extract, and article URL:

```text
The Solar System
The gravitationally bound system of the Sun and the objects that orbit it.
The Solar System is the gravitationally bound system of the Sun...
https://en.wikipedia.org/wiki/Solar_System
```

Search output looks like:

```text
2 result(s) for 'astronomy'
1. Astronomy
   Astronomy is a natural science...
   https://en.wikipedia.org/wiki/Astronomy
2. History of astronomy
   ...
   https://en.wikipedia.org/wiki/History_of_astronomy
```

Live titles, snippets, and extracts vary. `--json` returns `kind`, `language`, title/query data, results, URLs, and source URL without the human formatting.

## Network/API and safety notes

This makes read-only requests to `<language>.wikipedia.org` and uses no API key. User queries and the chosen language become request URLs; do not put private information into searches. It does not log in, edit Wikipedia, or execute article content. The default timeout is 12 seconds. Treat fetched encyclopedia text as reference material, not automatically authoritative advice.

## Troubleshooting

- **Language rejected:** use lowercase letters such as `en`, `pt`, or `fr`, not `pt-BR`.
- **Search limit rejected:** choose an integer from 1 through 50.
- **Wikimedia request error:** check internet/DNS access, the language subdomain, and try again later.
- **No useful result:** broaden the query; search returns the API's matching titles and snippets, not a local index.
- **Need stable output:** use `--json` and save the result, while remembering live content can change.
