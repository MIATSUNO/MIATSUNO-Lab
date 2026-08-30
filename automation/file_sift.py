import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


CATEGORIES = {
    "documents": {".doc", ".docx", ".odt", ".pdf", ".rtf", ".tex", ".txt", ".wpd"},
    "images": {".bmp", ".gif", ".heic", ".jpeg", ".jpg", ".png", ".raw", ".svg", ".tif", ".tiff", ".webp"},
    "audio": {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav", ".wma"},
    "video": {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm", ".wmv"},
    "archives": {".7z", ".bz2", ".gz", ".rar", ".tar", ".xz", ".zip"},
    "code": {".c", ".cc", ".cpp", ".css", ".go", ".h", ".hpp", ".html", ".java", ".js", ".json", ".jsx", ".md", ".php", ".py", ".rb", ".rs", ".sh", ".sql", ".ts", ".tsx", ".xml", ".yaml", ".yml"},
    "data": {".csv", ".db", ".sqlite", ".sqlite3", ".tsv", ".xls", ".xlsx"},
}


def category_for(path):
    suffix = path.suffix.lower()
    for category, suffixes in CATEGORIES.items():
        if suffix in suffixes:
            return category
    return "other"


def timestamp():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def path_is_within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def collect_files(source, destination, recursive):
    iterator = source.rglob("*") if recursive else source.iterdir()
    result = []
    for candidate in iterator:
        try:
            if candidate.is_symlink() or not candidate.is_file():
                continue
            if path_is_within(candidate.resolve(), destination):
                continue
            result.append(candidate)
        except OSError as exc:
            print(f"Unable to inspect {candidate}: {exc}", file=sys.stderr)
    return sorted(result, key=lambda item: str(item).casefold())


def write_json_atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def choose_target(path, reserved):
    candidate = path
    number = 1
    while candidate.exists() or str(candidate).casefold() in reserved:
        candidate = path.with_name(f"{path.stem} ({number}){path.suffix}")
        number += 1
    reserved.add(str(candidate).casefold())
    return candidate


def organize(args):
    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_dir():
        print(f"Source directory does not exist or is not a directory: {source}", file=sys.stderr)
        return 2
    destination = Path(args.destination).expanduser().resolve() if args.destination else source.parent / f"{source.name}_organized"
    if destination == source or path_is_within(destination, source):
        print("Destination must be outside the source directory.", file=sys.stderr)
        return 2
    files = collect_files(source, destination, args.recursive)
    reserved = set()
    operations = []
    for original in files:
        category = category_for(original)
        target = choose_target(destination / category / original.name, reserved)
        operations.append({"source": str(original), "destination": str(target), "category": category})
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else destination / f"file-sift-manifest-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    if args.dry_run:
        print(f"Dry run: {len(operations)} file(s) would be organized.")
        for operation in operations:
            print(f"{operation['source']} -> {operation['destination']}")
        return 0
    successful = []
    failures = 0
    for operation in operations:
        source_path = Path(operation["source"])
        destination_path = Path(operation["destination"])
        try:
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            if destination_path.exists():
                raise FileExistsError(f"Collision detected at {destination_path}")
            shutil.move(str(source_path), str(destination_path))
            successful.append(operation)
            print(f"Moved {source_path} -> {destination_path}")
        except (OSError, shutil.Error) as exc:
            failures += 1
            print(f"Unable to move {source_path}: {exc}", file=sys.stderr)
    manifest = {
        "version": 1,
        "created_at": timestamp(),
        "source_root": str(source),
        "destination_root": str(destination),
        "recursive": bool(args.recursive),
        "operations": successful,
    }
    try:
        write_json_atomic(manifest_path, manifest)
        print(f"Manifest: {manifest_path}")
    except OSError as exc:
        print(f"Files were moved but the manifest could not be written: {exc}", file=sys.stderr)
        return 1
    print(f"Organized {len(successful)} file(s); {failures} failure(s).")
    return 1 if failures else 0


def load_manifest(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read manifest {path}: {exc}") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("operations"), list):
        raise ValueError("Manifest has an invalid format.")
    return manifest


def undo(args):
    manifest_path = Path(args.manifest).expanduser().resolve()
    try:
        manifest = load_manifest(manifest_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    operations = manifest["operations"]
    if args.dry_run:
        print(f"Dry run: {len(operations)} file(s) would be restored.")
        for operation in reversed(operations):
            print(f"{operation.get('destination')} -> {operation.get('source')}")
        return 0
    restored = 0
    failures = 0
    for operation in reversed(operations):
        current_value = operation.get("destination")
        original_value = operation.get("source")
        if not isinstance(current_value, str) or not isinstance(original_value, str) or not current_value or not original_value:
            failures += 1
            print("Manifest operation is missing a path.", file=sys.stderr)
            continue
        current = Path(current_value).expanduser()
        original = Path(original_value).expanduser()
        if not current.exists() and not current.is_symlink():
            failures += 1
            print(f"Cannot restore missing file: {current}", file=sys.stderr)
            continue
        if not current.is_file() and not current.is_symlink():
            failures += 1
            print(f"Cannot restore a non-file path: {current}", file=sys.stderr)
            continue
        if original.exists() or original.is_symlink():
            if not args.overwrite:
                failures += 1
                print(f"Original path already exists; use --overwrite to replace it: {original}", file=sys.stderr)
                continue
            if original.is_dir() and not original.is_symlink():
                failures += 1
                print(f"Cannot overwrite directory: {original}", file=sys.stderr)
                continue
            try:
                original.unlink()
            except OSError as exc:
                failures += 1
                print(f"Unable to remove existing {original}: {exc}", file=sys.stderr)
                continue
        try:
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(current), str(original))
            restored += 1
            print(f"Restored {current} -> {original}")
        except (OSError, shutil.Error) as exc:
            failures += 1
            print(f"Unable to restore {current}: {exc}", file=sys.stderr)
    print(f"Restored {restored} file(s); {failures} failure(s).")
    return 1 if failures else 0


def build_parser():
    parser = argparse.ArgumentParser(prog="file_sift", description="Organize files into type-based folders with reversible JSON manifests.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    organize_parser = subparsers.add_parser("organize", help="Plan or perform file organization")
    organize_parser.add_argument("source", help="Directory whose files should be organized")
    organize_parser.add_argument("-d", "--destination", help="Output directory; defaults to a sibling named SOURCE_organized")
    organize_parser.add_argument("-r", "--recursive", action="store_true", help="Include files in subdirectories")
    organize_parser.add_argument("--dry-run", action="store_true", default=True, help="Show planned moves without changing files (default)")
    organize_parser.add_argument("--apply", action="store_false", dest="dry_run", help="Perform the moves")
    organize_parser.add_argument("-m", "--manifest", help="Manifest path for applied moves")
    organize_parser.set_defaults(func=organize)
    for name in ("undo", "restore"):
        undo_parser = subparsers.add_parser(name, help="Restore moves recorded in a JSON manifest")
        undo_parser.add_argument("manifest", help="Path to a file-sift JSON manifest")
        undo_parser.add_argument("--dry-run", action="store_true", help="Show planned restorations without changing files")
        undo_parser.add_argument("--overwrite", action="store_true", help="Replace an existing original file")
        undo_parser.set_defaults(func=undo)
    return parser


def main(argv=None):
    try:
        arguments = build_parser().parse_args(argv)
        return arguments.func(arguments)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
