# local_toolbox

A harmless local toolbox for four everyday jobs: hashing a file, counting text statistics, displaying a bounded directory tree, and validating/formatting JSON.

## Installation

Requires Python 3.9 or newer. The program uses only the standard library.

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 local_toolbox.py --help
```

## Usage

The exact command help is:

```text
usage: local_toolbox.py [-h] {hash,stats,tree,format-json} ...

A local toolbox for hashes, file stats, directory trees, and JSON formatting.

positional arguments:
  {hash,stats,tree,format-json}
    hash                hash one local file
    stats               count bytes, lines, and words in one UTF-8 file
    tree                print a local directory tree
    format-json         validate and pretty-print one JSON file

options:
  -h, --help            show this help message and exit
```

Each subcommand has its own exact options via `python3 local_toolbox.py SUBCOMMAND --help`.

## Examples

```bash
python3 local_toolbox.py hash ./archive.zip --algorithm sha256
python3 local_toolbox.py stats ./notes.txt
python3 local_toolbox.py tree . --depth 2
python3 local_toolbox.py format-json settings.json --output settings.pretty.json
```

## Audience

Developers, students, and careful desktop users who need small local file utilities without installing a larger framework.

## Limitations

Hashing reads the file but does not prove that it came from a trusted source. Text statistics decode invalid UTF-8 bytes with replacement. Tree output is intentionally bounded by `--depth` and skips symlink recursion. JSON formatting replaces the destination file if it already exists.

## Safety notes

All operations are local and read-only except `format-json --output`, which writes exactly the formatted JSON to the path you choose. Check paths before running and do not use an output path that contains valuable uncommitted work.
