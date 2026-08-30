"""Maintain a small searchable local library of text snippets."""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class SnippetError(Exception):
    """A recoverable snippet storage error."""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def storage_path(value):
    selected = value or os.environ.get("SNIPPET_BOX_FILE") or "~/.local/share/snippet-box/snippets.json"
    return Path(selected).expanduser()


def load(path):
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise SnippetError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or not all(isinstance(key, str) and isinstance(value, dict) for key, value in data.items()):
        raise SnippetError(f"invalid snippet database: {path}")
    return data


def save(path, data):
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                temporary = None
        raise SnippetError(f"cannot write {path}: {exc}") from exc


def tags(value):
    return sorted({item.strip() for item in value.split(",") if item.strip()}) if value else []


def record(name, text, tag_value):
    timestamp = now()
    return {"name": name, "text": text, "tags": tags(tag_value), "created_at": timestamp, "updated_at": timestamp}


def display(item):
    print(f"{item['name']} [{', '.join(item.get('tags', []))}]")
    print(item["text"])
    print(f"updated {item.get('updated_at', 'unknown')}")


def import_data(source):
    try:
        with source.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise SnippetError(f"cannot import {source}: {exc}") from exc
    if not isinstance(value, dict) or not all(isinstance(key, str) and isinstance(item, dict) for key, item in value.items()):
        raise SnippetError("import must contain a snippet object")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create, search, and export a local JSON snippet library.")
    parser.add_argument("--file", help="Database path; otherwise SNIPPET_BOX_FILE or ~/.local/share/snippet-box/snippets.json.")
    commands = parser.add_subparsers(dest="command", required=True)
    add_parser = commands.add_parser("add", help="Create or replace a snippet.")
    add_parser.add_argument("name")
    add_parser.add_argument("--text", help="Snippet text; read standard input when omitted.")
    add_parser.add_argument("--tags", help="Comma-separated tags.")
    get_parser = commands.add_parser("get", help="Print one snippet.")
    get_parser.add_argument("name")
    list_parser = commands.add_parser("list", help="List snippet names.")
    list_parser.add_argument("--tag")
    search_parser = commands.add_parser("search", help="Search names, text, and tags.")
    search_parser.add_argument("query")
    remove_parser = commands.add_parser("remove", help="Delete one snippet.")
    remove_parser.add_argument("name")
    export_parser = commands.add_parser("export", help="Write the complete database to a JSON file.")
    export_parser.add_argument("path", type=Path)
    import_parser = commands.add_parser("import", help="Merge or replace the database from a JSON file.")
    import_parser.add_argument("path", type=Path)
    import_parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    path = storage_path(args.file)
    try:
        data = load(path)
        if args.command == "add":
            text = args.text if args.text is not None else sys.stdin.read()
            if not text.strip():
                raise SnippetError("snippet text cannot be empty")
            previous = data.get(args.name)
            item = record(args.name, text, args.tags)
            if previous:
                item["created_at"] = previous.get("created_at", item["created_at"])
            data[args.name] = item
            save(path, data)
            print(f"saved {args.name} in {path}")
        elif args.command == "get":
            if args.name not in data:
                raise SnippetError(f"snippet not found: {args.name}")
            display(data[args.name])
        elif args.command == "list":
            selected = [item for item in data.values() if not args.tag or args.tag in item.get("tags", [])]
            for item in sorted(selected, key=lambda entry: entry["name"].casefold()):
                print(f"{item['name']}\t{', '.join(item.get('tags', []))}")
            print(f"{len(selected)} snippet(s)")
        elif args.command == "search":
            needle = args.query.casefold()
            selected = [item for item in data.values() if needle in json.dumps(item, ensure_ascii=False).casefold()]
            for item in sorted(selected, key=lambda entry: entry["name"].casefold()):
                print(f"{item['name']}\t{', '.join(item.get('tags', []))}")
            print(f"{len(selected)} match(es)")
        elif args.command == "remove":
            if args.name not in data:
                raise SnippetError(f"snippet not found: {args.name}")
            del data[args.name]
            save(path, data)
            print(f"removed {args.name} from {path}")
        elif args.command == "export":
            save(args.path.expanduser(), data)
            print(f"exported {len(data)} snippet(s) to {args.path.expanduser()}")
        elif args.command == "import":
            incoming = import_data(args.path.expanduser())
            data = incoming if args.replace else {**data, **incoming}
            save(path, data)
            print(f"imported {len(incoming)} snippet(s) into {path}")
    except SnippetError as exc:
        parser.exit(1, f"snippet-box: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

