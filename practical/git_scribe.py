"""Turn a local Git repository into a concise factual report."""

import argparse
import json
import os
import subprocess
from pathlib import Path


class GitScribeError(Exception):
    """A recoverable repository inspection error."""


def run_git(repo, *arguments):
    command = ["git", "-C", str(repo), *arguments]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise GitScribeError(f"unable to start git: {exc}") from exc
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit status {completed.returncode}"
        raise GitScribeError(detail)
    return completed.stdout.strip()


def lines(value):
    return [line for line in value.splitlines() if line]


def build_report(repo, limit):
    root = Path(run_git(repo, "rev-parse", "--show-toplevel"))
    branch = run_git(root, "branch", "--show-current") or "detached HEAD"
    status_lines = lines(run_git(root, "status", "--short"))
    log_records = []
    log_value = run_git(root, "log", f"-{limit}", "--date=iso-strict", "--pretty=format:%H%x09%ad%x09%an%x09%s")
    for record in lines(log_value):
        commit, date, author, subject = (record.split("\t", 3) + [""] * 4)[:4]
        log_records.append({"commit": commit, "date": date, "author": author, "subject": subject})
    remotes = lines(run_git(root, "remote", "-v"))
    return {
        "repository": str(root),
        "branch": branch,
        "clean": not status_lines,
        "status": status_lines,
        "recent_commits": log_records,
        "remotes": remotes,
    }


def print_text(report):
    print(f"repository: {report['repository']}")
    print(f"branch: {report['branch']}")
    print(f"working tree: {'clean' if report['clean'] else 'changes present'}")
    if report["status"]:
        print("status:")
        for item in report["status"]:
            print(f"  {item}")
    print("recent commits:")
    for commit in report["recent_commits"]:
        print(f"  {commit['commit'][:12]} {commit['date']} {commit['author']}: {commit['subject']}")
    if report["remotes"]:
        print("remotes:")
        for remote in report["remotes"]:
            print(f"  {remote}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Report the real state and recent history of a local Git repository.")
    parser.add_argument("repo", nargs="?", default=os.getcwd(), help="Repository directory, defaulting to the current directory.")
    parser.add_argument("--limit", type=int, default=8, help="Number of recent commits to include.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    try:
        report = build_report(Path(args.repo).expanduser().resolve(), args.limit)
    except GitScribeError as exc:
        parser.exit(1, f"git-scribe: {exc}\n")
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

