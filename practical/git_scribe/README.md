# git_scribe

`git_scribe` turns the current state of a local Git repository into a concise factual report: repository root, branch, working-tree status, recent commits, and remotes. It shells out to the installed `git`; it does not make commits or change files.

## Prerequisites and installation

You need Python 3 and Git available on your PATH:

```bash
python3 --version
git --version
```

The script has no third-party Python dependencies. Run it from the checkout as `python3 practical/git_scribe.py`.

## Basic command

The real help is:

```text
usage: practical/git_scribe.py [-h] [--limit LIMIT] [--json] [repo]
```

Report the current repository (the default is the current directory), or name one explicitly:

```bash
python3 practical/git_scribe.py
python3 practical/git_scribe.py ~/src/my-project --limit 5
python3 practical/git_scribe.py . --json
```

The only flags are the help-listed `--limit` and `--json`; `--limit` must be at least 1.

## Input and output

The optional `repo` can be any directory inside a Git worktree. The tool runs `git -C` commands to find the top-level root, current branch (or `detached HEAD`), short status lines, up to the requested number of commits, and `remote -v` output.

Human output has this shape:

```text
repository: /home/me/src/project
branch: main
working tree: clean
recent commits:
  a1b2c3d4e5f6 2026-08-30T13:40:00+00:00 Mganga: Add useful README
remotes:
  origin https://github.com/example/project.git (fetch)
```

A dirty worktree says `working tree: changes present` and includes a `status:` section. JSON returns the same facts as structured fields: `repository`, `branch`, `clean`, `status`, `recent_commits`, and `remotes`. Git errors produce a `git-scribe: ...` message and exit 1.

## Safety notes

This is local-only and read-only: it invokes `rev-parse`, `branch`, `status`, `log`, and `remote`, never `git add`, commit, checkout, fetch, or push. Reports can include remote URLs and commit author/subjects, so review JSON before sharing it publicly.

## Troubleshooting

- **“unable to start git”:** install Git and ensure it is on PATH.
- **Not a repository:** pass a directory inside a Git worktree, not an arbitrary folder.
- **Detached branch name:** `detached HEAD` is the actual state, not an error.
- **No recent commits/remotes:** an empty history or repository without remotes is valid; the corresponding sections may simply be empty.
- **`--limit` rejected:** use a positive integer, at least 1.
