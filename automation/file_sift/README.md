# file_sift

`file_sift` is a small, reversible organizer for a messy folder. It classifies files by extension, moves them into folders such as `documents`, `images`, `code`, and `other`, and writes a JSON manifest so you can put the moves back.

## Prerequisites and installation

You need Python 3 and a directory you are allowed to read and write. The script only uses Python's standard library, so there is nothing to install:

```bash
python3 --version
```

Run it from the repository checkout, or use the full path `python3 automation/file_sift.py`.

## Basic commands

The command-line interface reports this usage:

```text
usage: file_sift [-h] {organize,undo,restore} ...

file_sift organize SOURCE [-d DESTINATION] [-r] [--dry-run] [--apply] [-m MANIFEST]
file_sift undo MANIFEST [--dry-run] [--overwrite]
file_sift restore MANIFEST [--dry-run] [--overwrite]
```

`organize` is a dry run by default. Preview a folder first:

```bash
python3 automation/file_sift.py organize ~/Downloads
```

Include subdirectories and choose an output folder, then actually move files:

```bash
python3 automation/file_sift.py organize ~/Downloads -r -d ~/Downloads_organized --apply
```

You can choose where the applied manifest is written with `-m MANIFEST`. To preview or undo it later, both `undo` and `restore` accept the manifest path:

```bash
python3 automation/file_sift.py undo ~/Downloads_organized/file-sift-manifest-20260830T134500Z.json --dry-run
python3 automation/file_sift.py restore ~/Downloads_organized/file-sift-manifest-20260830T134500Z.json
```

The options shown by the real help are `-d/--destination`, `-r/--recursive`, `--dry-run`, `--apply`, `-m/--manifest`, and (for restoration) `--overwrite`.

## What goes in and what comes out

It reads regular files from the source directory. Without `-r`, it reads only that directory; with `-r`, it walks subdirectories. Extensions are matched case-insensitively against the built-in categories; unknown extensions go to `other`. Symlinks and non-files are skipped. The destination must be outside the source.

A preview looks like this (paths depend on your machine):

```text
Dry run: 2 file(s) would be organized.
/home/me/Downloads/report.pdf -> /home/me/Downloads_organized/documents/report.pdf
/home/me/Downloads/photo.jpg -> /home/me/Downloads_organized/images/photo.jpg
```

With `--apply`, it prints `Moved ...` lines, creates category directories, and writes a JSON manifest. Name collisions get `photo (1).jpg`, `photo (2).jpg`, and so on. `undo`/`restore` process the manifest in reverse order and print `Restored ...`; they refuse to overwrite an existing original unless you pass `--overwrite`.

## Safety notes

Start with the default dry run. `--apply` uses `shutil.move`, so it really changes the filesystem. The destination cannot be the source or inside it, and the collector skips the destination to avoid reprocessing its own output. Keep the manifest until you are sure the result is right. This tool has no network access and no API calls.

## Troubleshooting

- **“Destination must be outside…”** Pick a sibling or another directory, not a folder inside the source.
- **Nothing is listed:** add `-r` if the files are nested, and remember symlinks are intentionally skipped.
- **The original already exists during restore:** inspect first with `--dry-run`, then use `--overwrite` only if replacing that file is really wanted.
- **The manifest cannot be read:** check that it is the JSON file produced by an applied run and that the path is correct.
