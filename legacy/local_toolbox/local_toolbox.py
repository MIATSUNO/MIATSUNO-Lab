#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import sys


def hash_file(path, algorithm, chunk_size):
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def print_tree(root, depth, prefix=""):
    if depth < 0:
        return
    try:
        entries = sorted(root.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
    except OSError as error:
        print(prefix + "[unreadable: " + str(error) + "]")
        return
    for index, entry in enumerate(entries):
        marker = "└── " if index == len(entries) - 1 else "├── "
        print(prefix + marker + entry.name + ("/" if entry.is_dir() else ""))
        if entry.is_dir() and depth > 0 and not entry.is_symlink():
            extension = "    " if index == len(entries) - 1 else "│   "
            print_tree(entry, depth - 1, prefix + extension)


def file_stats(path):
    data = path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    lines = 0 if not text else text.count("\n") + (0 if text.endswith("\n") else 1)
    words = len(text.split())
    print("path:", path)
    print("bytes:", len(data))
    print("lines:", lines)
    print("words:", words)


def format_json(input_path, output_path):
    with input_path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    rendered = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if output_path:
        output_path.write_text(rendered, encoding="utf-8")
        print("wrote:", output_path)
    else:
        sys.stdout.write(rendered)


def build_parser():
    parser = argparse.ArgumentParser(description="A local toolbox for hashes, file stats, directory trees, and JSON formatting.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    hash_parser = subparsers.add_parser("hash", help="hash one local file")
    hash_parser.add_argument("path", type=Path, help="file to read")
    hash_parser.add_argument("--algorithm", choices=("sha256", "sha512", "blake2b"), default="sha256", help="digest algorithm (default: sha256)")
    stats_parser = subparsers.add_parser("stats", help="count bytes, lines, and words in one UTF-8 file")
    stats_parser.add_argument("path", type=Path, help="file to read")
    tree_parser = subparsers.add_parser("tree", help="print a local directory tree")
    tree_parser.add_argument("path", type=Path, help="directory to display")
    tree_parser.add_argument("--depth", type=int, default=2, help="nested directory levels (default: 2)")
    json_parser = subparsers.add_parser("format-json", help="validate and pretty-print one JSON file")
    json_parser.add_argument("input", type=Path, help="JSON file to read")
    json_parser.add_argument("--output", type=Path, help="write formatted JSON here instead of stdout")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "hash":
        if not args.path.is_file():
            parser.error("hash path must be a file")
        print(hash_file(args.path, args.algorithm, 1024 * 1024))
    elif args.command == "stats":
        if not args.path.is_file():
            parser.error("stats path must be a file")
        file_stats(args.path)
    elif args.command == "tree":
        if not args.path.is_dir():
            parser.error("tree path must be a directory")
        if args.depth < 0 or args.depth > 20:
            parser.error("--depth must be between 0 and 20")
        print(args.path)
        print_tree(args.path, args.depth)
    else:
        if not args.input.is_file():
            parser.error("input must be a file")
        try:
            format_json(args.input, args.output)
        except json.JSONDecodeError as error:
            print("invalid JSON:", error, file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

