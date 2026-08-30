# snippet_box

`snippet_box` is a tiny searchable local library for commands, notes, and other text you keep retyping. It stores named snippets as JSON, supports tags, and can export/import the whole database.

## Prerequisites and installation

Python 3 is enough; this is standard-library only:

```bash
python3 --version
```

No pip install is required. Run it as `python3 practical/snippet_box.py`.

## Basic commands

The real help reports:

```text
usage: practical/snippet_box.py [-h] [--file FILE]
                                {add,get,list,search,remove,export,import} ...
```

The database path is `--file`, then one of the help-listed commands:

```bash
python3 practical/snippet_box.py --file ./snippets.json add deploy --text 'python3 -m app' --tags python,ops
python3 practical/snippet_box.py --file ./snippets.json get deploy
python3 practical/snippet_box.py --file ./snippets.json list --tag ops
python3 practical/snippet_box.py --file ./snippets.json search python
python3 practical/snippet_box.py --file ./snippets.json export ./snippets-backup.json
python3 practical/snippet_box.py --file ./snippets.json remove deploy
python3 practical/snippet_box.py --file ./snippets.json import ./snippets-backup.json
```

`add` accepts `--text` and `--tags`; `import` accepts `--replace`. If `--text` is omitted, `add` reads standard input. Without `--file`, it uses `SNIPPET_BOX_FILE`, then `~/.local/share/snippet-box/snippets.json`.

## Input and output

`add NAME` creates or replaces a record containing `name`, `text`, sorted comma-separated `tags`, and UTC `created_at`/`updated_at` timestamps. `get` prints the name/tags, text, and `updated ...`. `list` sorts by name and ends with a count; `search` looks case-insensitively through name, text, and tags.

For the commands above, output is shaped like:

```text
saved deploy in snippets.json
deploy [ops, python]
python3 -m app
updated 2026-08-30T13:45:00+00:00
1 snippet(s)
```

`export` writes the complete JSON database. `import` merges incoming names by default; `--replace` uses the imported object as the complete database. Writes use a temporary file and replacement, so a normal save is atomic.

## Safety notes

Everything is local; there is no network or API. The tool reads and writes the selected JSON file, and `remove` is destructive to that record, so export a backup first if it matters. Snippets may contain passwords or tokens—do not store secrets casually, and protect the file's filesystem permissions. Import data only from a source you trust.

## Troubleshooting

- **Database path surprises you:** pass `--file` explicitly or inspect `SNIPPET_BOX_FILE`.
- **“snippet text cannot be empty”:** pass non-whitespace `--text`, or pipe text to stdin.
- **“snippet not found”:** list names first; matching is exact for `get` and `remove`.
- **Import errors:** the file must contain a JSON object whose values are snippet objects.
- **Unreadable/invalid database:** restore a known-good export or choose a new `--file`.
