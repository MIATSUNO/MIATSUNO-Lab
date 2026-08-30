import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def timestamp():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def path_is_within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def relative_name(path, root):
    return path.relative_to(root).as_posix()


def safe_relative(value):
    if not isinstance(value, str) or not value:
        raise ValueError(f"Unsafe archive path: {value!r}")
    normalized = value.replace("\\", "/")
    path = Path(normalized)
    if normalized.startswith("/") or path.is_absolute() or any(part in {"", ".", ".."} for part in normalized.split("/") + list(path.parts)):
        raise ValueError(f"Unsafe archive path: {value!r}")
    return normalized


def matches_exclusion(relative, patterns):
    parts = relative.split("/")
    for pattern in patterns:
        normalized = pattern.replace("\\", "/").strip("/")
        if not normalized:
            continue
        if fnmatch.fnmatch(relative, normalized) or fnmatch.fnmatch(parts[-1], normalized):
            return True
        if any(fnmatch.fnmatch(part, normalized) for part in parts):
            return True
    return False


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def load_state(path):
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read state file {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("files"), dict):
        raise ValueError("State file has an invalid format.")
    return value


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def scan_source(source, destination, state_path, patterns):
    records = {}
    errors = []
    destination = destination.resolve()
    state_path = state_path.resolve()

    def walk_error(error):
        errors.append(f"Unable to scan {error.filename}: {error.strerror or error}")

    for root, directories, filenames in os.walk(source, topdown=True, followlinks=False, onerror=walk_error):
        root_path = Path(root)
        retained_directories = []
        for directory in directories:
            directory_path = root_path / directory
            try:
                if directory_path.is_symlink():
                    continue
                relative_directory = relative_name(directory_path, source)
                if path_is_within(directory_path.resolve(), destination) or matches_exclusion(relative_directory, patterns):
                    continue
                retained_directories.append(directory)
            except OSError as exc:
                errors.append(f"Unable to inspect {directory_path}: {exc}")
        directories[:] = retained_directories
        for filename in filenames:
            file_path = root_path / filename
            try:
                if file_path.is_symlink() or not file_path.is_file():
                    continue
                resolved = file_path.resolve()
                relative = relative_name(file_path, source)
                if path_is_within(resolved, destination) or resolved == state_path or matches_exclusion(relative, patterns):
                    continue
                stat = file_path.stat()
                records[relative] = {"sha256": sha256_file(file_path), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
            except (OSError, ValueError) as exc:
                errors.append(f"Unable to read {file_path}: {exc}")
    return records, errors


def archive_name(destination):
    base = datetime.now(timezone.utc).strftime("backup-%Y%m%dT%H%M%SZ")
    candidate = destination / f"{base}.zip"
    number = 1
    while candidate.exists():
        candidate = destination / f"{base}-{number}.zip"
        number += 1
    return candidate


def compression_value(name):
    return {"store": zipfile.ZIP_STORED, "deflate": zipfile.ZIP_DEFLATED, "bzip2": zipfile.ZIP_BZIP2, "lzma": zipfile.ZIP_LZMA}[name]


def make_manifest(source, mode, records, deleted, archive, exclusions):
    entries = []
    for relative in sorted(records):
        entries.append({"path": relative, "sha256": records[relative]["sha256"], "size": records[relative]["size"], "mtime_ns": records[relative]["mtime_ns"]})
    return {"version": 2, "created_at": timestamp(), "source_root": str(source), "mode": mode, "archive": archive.name, "exclusions": sorted(exclusions), "files": entries, "deleted": sorted(deleted)}


def validate_manifest(manifest):
    if not isinstance(manifest, dict) or manifest.get("version") not in {1, 2}:
        raise ValueError("Archive manifest has an unsupported format.")
    if manifest.get("mode") not in {"full", "incremental"} or not isinstance(manifest.get("files"), list) or not isinstance(manifest.get("deleted", []), list):
        raise ValueError("Archive manifest has an invalid format.")
    names = set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict):
            raise ValueError("Archive manifest contains an invalid file entry.")
        relative = safe_relative(entry.get("path"))
        if relative in names or not isinstance(entry.get("sha256"), str) or len(entry["sha256"]) != 64 or not isinstance(entry.get("size"), int) or entry["size"] < 0:
            raise ValueError("Archive manifest contains an invalid file entry.")
        names.add(relative)
    for relative in manifest.get("deleted", []):
        safe_relative(relative)
    return manifest


def write_archive(path, source, manifest, compression):
    manifest_bytes = json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
    with zipfile.ZipFile(path, "w", compression=compression, compresslevel=6) as archive:
        for entry in manifest["files"]:
            archive.write(source / Path(entry["path"]), arcname=entry["path"])
        archive.writestr("manifest.json", manifest_bytes)


def read_manifest_from_archive(path):
    try:
        with zipfile.ZipFile(path, "r") as archive:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    except (OSError, zipfile.BadZipFile, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read archive manifest {path}: {exc}") from exc
    return validate_manifest(manifest)


def verify_archive(path, manifest):
    expected = {entry["path"] for entry in manifest["files"]}
    expected.add("manifest.json")
    with zipfile.ZipFile(path, "r") as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive CRC verification failed.")
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != expected:
            raise ValueError("Archive members do not match its manifest.")
        stored_manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        if stored_manifest != manifest:
            raise ValueError("Archive manifest contents do not match the planned backup.")
        for entry in manifest["files"]:
            with archive.open(entry["path"], "r") as handle:
                digest = hashlib.sha256()
                size = 0
                while True:
                    block = handle.read(1024 * 1024)
                    if not block:
                        break
                    size += len(block)
                    digest.update(block)
            if size != entry["size"] or digest.hexdigest() != entry["sha256"]:
                raise ValueError(f"Verification failed for {entry['path']}.")


def create_backup(args):
    source = Path(args.source).expanduser().resolve()
    destination = Path(args.destination).expanduser().resolve()
    if not source.exists() or not source.is_dir():
        print(f"Source directory does not exist or is not a directory: {source}", file=sys.stderr)
        return 2
    if destination == source or path_is_within(destination, source):
        print("Destination must be outside the source directory.", file=sys.stderr)
        return 2
    try:
        destination.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Unable to create destination: {exc}", file=sys.stderr)
        return 1
    state_path = Path(args.state).expanduser().resolve() if args.state else destination / ".backup_buddy_state.json"
    try:
        previous = None if args.reset else load_state(state_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if previous and previous.get("source_root") != str(source):
        print(f"State belongs to a different source directory: {previous.get('source_root')}", file=sys.stderr)
        return 2
    patterns = list(args.exclude)
    records, errors = scan_source(source, destination, state_path, patterns)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    old_records = (previous or {}).get("files", {})
    old_backups = (previous or {}).get("backups", [])
    if not isinstance(old_records, dict) or not isinstance(old_backups, list):
        print("State file has invalid records.", file=sys.stderr)
        return 2
    if args.full or not previous:
        selected = records
        mode = "full"
    else:
        selected = {path: record for path, record in records.items() if old_records.get(path, {}).get("sha256") != record["sha256"]}
        mode = "incremental"
    deleted = sorted(set(old_records) - set(records)) if previous and not args.full else []
    if not selected and not deleted:
        if args.dry_run:
            print("Dry run: no changes require a backup archive.")
            return 0
        state = {"version": 2, "source_root": str(source), "files": records, "backups": old_backups, "exclusions": sorted(patterns), "updated_at": timestamp()}
        try:
            save_state(state_path, state)
        except OSError as exc:
            print(f"Unable to save state: {exc}", file=sys.stderr)
            return 1
        print("No changes require a backup archive.")
        return 0
    archive_path = archive_name(destination)
    manifest = make_manifest(source, mode, selected, deleted, archive_path, patterns)
    if args.dry_run:
        print(f"Dry run: {len(selected)} file(s) and {len(deleted)} deletion(s) would be written to {archive_path}")
        for entry in manifest["files"]:
            print(f"ADD {entry['path']}")
        for path in manifest["deleted"]:
            print(f"DELETE {path}")
        return 0
    temporary = None
    committed_archive = False
    try:
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{archive_path.name}.", suffix=".tmp", dir=destination)
        os.close(descriptor)
        temporary = Path(temporary_name)
        write_archive(temporary, source, manifest, compression_value(args.compression))
        verify_archive(temporary, manifest)
        os.replace(temporary, archive_path)
        temporary = None
        committed_archive = True
        history = list(old_backups)
        history.append({"archive": archive_path.name, "created_at": manifest["created_at"], "mode": mode, "files": len(selected), "deleted": len(deleted)})
        state = {"version": 2, "source_root": str(source), "files": records, "backups": history, "exclusions": sorted(patterns), "updated_at": timestamp()}
        save_state(state_path, state)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        if committed_archive and archive_path.exists():
            try:
                archive_path.unlink()
            except OSError:
                committed_archive = False
        print(f"Backup failed and was not committed: {exc}", file=sys.stderr)
        return 1
    finally:
        if temporary is not None and temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                temporary = None
    print(f"Created and verified {archive_path}")
    print(f"Mode: {mode}; files: {len(selected)}; deletions: {len(deleted)}")
    print(f"State: {state_path}")
    return 0


def archive_sequence(destination, target):
    candidates = []
    for path in destination.glob("*.zip"):
        try:
            manifest = read_manifest_from_archive(path)
            candidates.append((manifest.get("created_at", ""), path, manifest))
        except ValueError:
            continue
    candidates.sort(key=lambda item: (item[0], item[1].name))
    target = target.resolve()
    selected = []
    found = False
    for _, path, manifest in candidates:
        selected.append((path, manifest))
        if path.resolve() == target:
            found = True
            break
    if not found:
        raise ValueError(f"Target archive was not found in {destination}.")
    if not selected or selected[0][1].get("mode") != "full":
        raise ValueError("Rollback requires a verified full archive before incremental archives.")
    return selected


def apply_archive_to_stage(path, manifest, stage, snapshot):
    if manifest["mode"] == "full":
        for child in stage.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        snapshot.clear()
    with zipfile.ZipFile(path, "r") as archive:
        for entry in manifest["files"]:
            relative = safe_relative(entry["path"])
            target = stage / Path(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(relative, "r") as source_handle, target.open("wb") as target_handle:
                shutil.copyfileobj(source_handle, target_handle, 1024 * 1024)
            actual = {"sha256": sha256_file(target), "size": target.stat().st_size, "mtime_ns": entry.get("mtime_ns", 0)}
            if actual["sha256"] != entry["sha256"] or actual["size"] != entry["size"]:
                raise ValueError(f"Verification failed while staging {relative}.")
            snapshot[relative] = actual
        for relative in manifest.get("deleted", []):
            safe = safe_relative(relative)
            target = stage / Path(safe)
            if target.exists() or target.is_symlink():
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            snapshot.pop(safe, None)


def source_without_exclusions(source, patterns):
    for root, directories, filenames in os.walk(source, topdown=True):
        root_path = Path(root)
        directories[:] = [name for name in directories if not matches_exclusion(relative_name(root_path / name, source), patterns)]
        for name in filenames:
            path = root_path / name
            relative = relative_name(path, source)
            if not matches_exclusion(relative, patterns):
                yield path


def rollback(args):
    target = Path(args.archive).expanduser().resolve()
    if not target.exists() or target.suffix.lower() != ".zip":
        print(f"Archive does not exist: {target}", file=sys.stderr)
        return 2
    destination = target.parent
    try:
        sequence = archive_sequence(destination, target)
        first_manifest = sequence[0][1]
        source = Path(args.source).expanduser().resolve() if args.source else Path(first_manifest["source_root"]).expanduser().resolve()
        patterns = list(args.exclude) if args.exclude else list(first_manifest.get("exclusions", []))
        snapshot = {}
        with tempfile.TemporaryDirectory(prefix=".backup-buddy-rollback-", dir=destination) as temporary:
            stage = Path(temporary)
            for path, manifest in sequence:
                verify_archive(path, manifest)
                apply_archive_to_stage(path, manifest, stage, snapshot)
            if args.dry_run:
                print(f"Dry run: rollback would restore {len(snapshot)} file(s) to {source}")
                return 0
            source.mkdir(parents=True, exist_ok=True)
            for path in list(source_without_exclusions(source, patterns)):
                path.unlink()
            for root, directories, filenames in os.walk(source, topdown=False):
                root_path = Path(root)
                for directory in directories:
                    directory_path = root_path / directory
                    if not matches_exclusion(relative_name(directory_path, source), patterns):
                        try:
                            directory_path.rmdir()
                        except OSError:
                            continue
            for root, directories, filenames in os.walk(stage):
                root_path = Path(root)
                relative_root = root_path.relative_to(stage)
                output_root = source / relative_root
                output_root.mkdir(parents=True, exist_ok=True)
                for name in filenames:
                    shutil.copy2(root_path / name, output_root / name)
            actual, errors = scan_source(source, destination, destination / ".rollback-state-ignore", patterns)
            if errors or set(actual) != set(snapshot):
                raise ValueError("Rollback verification found an unexpected file set.")
            for relative, expected in snapshot.items():
                if actual[relative]["sha256"] != expected["sha256"] or actual[relative]["size"] != expected["size"]:
                    raise ValueError(f"Rollback verification failed for {relative}.")
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Rollback failed: {exc}", file=sys.stderr)
        return 1
    print(f"Rolled back {source} using {target}")
    print(f"Restored files: {len(snapshot)}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="backup_buddy", description="Create verified full or incremental ZIP backups with exclusions and rollback.")
    parser.add_argument("source", help="Directory to back up")
    parser.add_argument("destination", help="Directory where ZIP archives and state are stored")
    parser.add_argument("--exclude", action="append", default=[], metavar="PATTERN", help="Exclude a path or filename pattern; may be repeated")
    parser.add_argument("--state", help="State JSON path (default: DESTINATION/.backup_buddy_state.json)")
    parser.add_argument("--full", action="store_true", help="Include every currently selected file instead of only changes")
    parser.add_argument("--reset", action="store_true", help="Ignore an existing state and begin a new full baseline")
    parser.add_argument("--compression", choices=("deflate", "store", "bzip2", "lzma"), default="deflate", help="ZIP compression method (default: deflate)")
    parser.add_argument("--dry-run", action="store_true", help="Show the planned backup without writing an archive or state")
    parser.set_defaults(func=create_backup)
    return parser


def build_rollback_parser():
    parser = argparse.ArgumentParser(prog="backup_buddy rollback", description="Restore a source directory to the state represented by an archive.")
    parser.add_argument("archive", help="Target ZIP archive")
    parser.add_argument("--source", help="Source directory; defaults to the archive manifest source")
    parser.add_argument("--exclude", action="append", default=[], metavar="PATTERN", help="Preserve excluded paths; defaults to archive exclusions")
    parser.add_argument("--dry-run", action="store_true", help="Verify and preview without changing the source")
    parser.set_defaults(func=rollback)
    return parser


def main(argv=None):
    values = list(sys.argv[1:] if argv is None else argv)
    if values and values[0] == "rollback":
        arguments = build_rollback_parser().parse_args(values[1:])
    else:
        arguments = build_parser().parse_args(values)
    try:
        return arguments.func(arguments)
    except KeyboardInterrupt:
        print("Interrupted; no backup was committed.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
