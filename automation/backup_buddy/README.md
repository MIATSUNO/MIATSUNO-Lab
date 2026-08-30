# backup_buddy

`backup_buddy` makes verified ZIP backups of a directory. The first run is a full baseline; later runs can be incremental, recording changed files and deletions. Each archive carries a manifest and is checked before it is committed. The `rollback` mode rebuilds a source directory from a full archive plus the incremental archives leading up to it.

## Prerequisites and installation

You need Python 3 with its standard library. ZIP compression support comes from Python's `zipfile`; no pip package is needed:

```bash
python3 --version
```

Run with `python3 automation/backup_buddy.py`.

## Basic commands

The real help starts with:

```text
usage: backup_buddy [-h] [--exclude PATTERN] [--state STATE] [--full]
                    [--reset] [--compression {deflate,store,bzip2,lzma}]
                    [--dry-run]
                    source destination
```

Preview the initial backup without writing anything:

```bash
python3 automation/backup_buddy.py ~/Documents ~/Backups --dry-run
```

Create it, excluding a cache path, then make a later full backup if needed:

```bash
python3 automation/backup_buddy.py ~/Documents ~/Backups --exclude .cache --exclude '*.tmp'
python3 automation/backup_buddy.py ~/Documents ~/Backups
python3 automation/backup_buddy.py ~/Documents ~/Backups --full --compression bzip2
```

The script also has a real `rollback` command:

```text
usage: backup_buddy rollback [-h] [--source SOURCE] [--exclude PATTERN]
                             [--dry-run]
                             archive
```

Preview and then apply a rollback:

```bash
python3 automation/backup_buddy.py rollback ~/Backups/backup-20260830T134500Z.zip --dry-run
python3 automation/backup_buddy.py rollback ~/Backups/backup-20260830T134500Z.zip
```

Help-listed options are repeatable `--exclude`, `--state`, `--full`, `--reset`, `--compression {deflate,store,bzip2,lzma}`, and `--dry-run`; rollback adds `--source`, `--exclude`, and `--dry-run`.

## Input and output

The source and destination are directories, and the destination must be outside the source. Selected files are hashed with SHA-256. Archives are named `backup-YYYYMMDDTHHMMSSZ.zip` (with a numeric suffix if needed), and the state defaults to `DESTINATION/.backup_buddy_state.json`.

A dry run reports the plan:

```text
Dry run: 2 file(s) and 1 deletion(s) would be written to /home/me/Backups/backup-20260830T134500Z.zip
ADD notes/today.txt
ADD photo.jpg
DELETE old.txt
```

A successful run prints `Created and verified ...`, its mode and counts, and the state path. The archive includes `manifest.json`; the tool checks CRCs, member names, sizes, and hashes. A rollback prints `Rolled back ...` and `Restored files: N`.

## Safety notes

Use `--dry-run` first. This tool reads files and writes ZIPs/state; rollback really removes selected files from the source before copying the staged snapshot back. It preserves paths matching exclusions. The archive path validation rejects absolute, empty, `.` and `..` components. Do not treat a ZIP from an untrusted source as automatically safe just because it has a manifest. There is no network or API access.

## Troubleshooting

- **Destination/source error:** choose a separate backup directory; nesting it under the source is rejected.
- **No archive created:** an incremental run prints `No changes require a backup archive.` when nothing changed.
- **State belongs to another source:** use a separate destination/state file, or intentionally start a new baseline with `--reset`.
- **Rollback says a full archive is required:** rollback needs the verified full archive that precedes the incremental chain in that destination.
- **Compression unavailable:** use the default `deflate` or `store`; the available choices are exactly those in help.
