#!/usr/bin/env python3
"""Snapshot and compare a working tree's dirty state by content, to prove a run was read-only.

Stdlib only. Read-only: hashes files, never writes inside the repo.

    python3 tree_state.py snapshot --repo DIR [--exclude PATH ...] > before.json
    python3 tree_state.py compare before.json --repo DIR [--exclude PATH ...]

`git status --porcelain` cannot do this job: it prints ` M` whether or not an already-modified file
changed again, and it collapses an untracked directory to one line. The snapshot records a content
hash for every modified, deleted and untracked file (each file listed separately), plus HEAD, so
editing a file that was already dirty, or leaving a probe test behind, shows up as a difference.

.edge-cases/ and reviews/edge-cases/ are always excluded; pass --exclude for a custom output
directory and for wiki/ when the run ingested into it.

Exit codes: snapshot 0. compare 0 identical, 1 differences (listed), 2 bad input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_EXCLUDES = (".edge-cases", "reviews/edge-cases")
SCHEMA = "edge-cases-tree/1"


def git(repo: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout


def file_hash(path: Path) -> str:
    if path.is_symlink():
        return "symlink:" + hashlib.sha1(str(path.readlink()).encode()).hexdigest()
    if not path.exists():
        return "<deleted>"
    if path.is_dir():
        return "<dir>"
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot(repo: Path, excludes: list[str]) -> dict:
    spec = ["--", ".", *(f":(exclude){p}" for p in dict.fromkeys([*DEFAULT_EXCLUDES, *excludes]))]
    rc, out = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames", *spec)
    if rc != 0:
        raise ValueError(f"{repo} is not a git working tree")
    files = {}
    for entry in out.split("\0"):
        if len(entry) > 3:
            rel = entry[3:]
            files[rel] = file_hash(repo / rel)
    _, head = git(repo, "rev-parse", "--verify", "--quiet", "HEAD")
    return {"schema": SCHEMA, "head": head.strip() or None, "files": dict(sorted(files.items()))}


def compare(before: dict, after: dict) -> list[str]:
    diffs = []
    if before.get("head") != after.get("head"):
        diffs.append(f"HEAD moved: {before.get('head')} -> {after.get('head')}")
    b, a = before.get("files", {}), after.get("files", {})
    for rel in sorted(set(b) | set(a)):
        if rel not in b:
            diffs.append(f"changed during the run: {rel}")
        elif rel not in a:
            diffs.append(f"reverted to HEAD during the run: {rel}")
        elif b[rel] != a[rel]:
            diffs.append(f"modified again during the run: {rel}")
    return diffs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["snapshot", "compare"])
    ap.add_argument("before", nargs="?", help="compare: the snapshot taken in pre-flight")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--exclude", action="append", default=[], metavar="PATH")
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    excludes = [e.strip("/") for e in args.exclude if e.strip("/")]
    try:
        now = snapshot(repo, excludes)
        if args.mode == "snapshot":
            json.dump(now, sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write("\n")
            return 0
        if not args.before:
            raise ValueError("compare needs the snapshot file from pre-flight")
        before = json.loads(Path(args.before).read_text(encoding="utf-8"))
        if before.get("schema") != SCHEMA:
            raise ValueError(f"{args.before} is not a {SCHEMA} snapshot")
    except (OSError, ValueError) as exc:
        print(f"tree_state: {exc}", file=sys.stderr)
        return 2
    diffs = compare(before, now)
    for d in diffs:
        print(d)
    print("tree unchanged" if not diffs else f"{len(diffs)} difference(s): the run was not read-only")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
