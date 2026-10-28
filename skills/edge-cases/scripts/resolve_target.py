#!/usr/bin/env python3
"""Resolve what an edge-case analysis is about, as one JSON document.

Stdlib only. Deterministic. Read-only: runs git plumbing and reads files, never writes.

    python3 resolve_target.py [<target>] [--target auto|feature|plan|changes] [--base <ref>]
                              [--repo <dir>] [--exclude <path> ...]

The skill's own output (.edge-cases/ and reviews/edge-cases/, plus every --exclude) is invisible to
every git query here: otherwise one run's report makes the next run's tree look dirty.

The detection order and every output field are documented in references/target-resolution.md.
Keep the two in step.

Exit codes: 0 resolved (including kind "ask" and an empty change set), 2 bad input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DOC_EXTS = {".md", ".markdown", ".txt", ".rst", ".adoc", ".pdf"}
SCOPES = {"uncommitted", "staged", "branch"}
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
GIT_NAMES = {"HEAD", "ORIG_HEAD", "FETCH_HEAD", "MERGE_HEAD", "@"}
HEX_SHA = re.compile(r"^[0-9a-f]{7,40}$")
IDENT = re.compile(r"^[A-Za-z_$][\w$]*(?:(?:\.|::|#)[A-Za-z_$][\w$]*)*$")
RANGE = re.compile(r"^(?P<a>[^.\s]+(?:\.[^.\s]+)*?)(?P<op>\.\.\.?)(?P<b>[^.\s]+(?:\.[^.\s]+)*)$")
DOC_DIRS = ("plans", "docs", "doc", "specs", "spec", "rfcs", "briefs")
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".venv", "venv", "target", "vendor", "__pycache__"}
DEFAULT_EXCLUDES = (".edge-cases", "reviews/edge-cases")
EXCLUDES: list[str] = list(DEFAULT_EXCLUDES)  # set once per run by resolve()
MAX_MATCHES = 20
MAX_UNTRACKED_BYTES = 2_000_000


class InputError(Exception):
    pass


# --------------------------------------------------------------------------- git helpers


def git(repo: Path, *args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return 127, ""
    return proc.returncode, proc.stdout


def git_ok(repo: Path, *args: str) -> str | None:
    rc, out = git(repo, *args)
    return out.strip() if rc == 0 else None


def is_git_repo(repo: Path) -> bool:
    return git_ok(repo, "rev-parse", "--is-inside-work-tree") == "true"


def commit_sha(repo: Path, ref: str) -> str | None:
    if ref.startswith("-"):
        return None
    return git_ok(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")


def current_branch(repo: Path) -> str | None:
    return git_ok(repo, "symbolic-ref", "--quiet", "--short", "HEAD")


def is_branch(repo: Path, name: str) -> bool:
    return any(
        git_ok(repo, "rev-parse", "--verify", "--quiet", f"{prefix}{name}") is not None
        for prefix in ("refs/heads/", "refs/remotes/")
    )


def default_base(repo: Path) -> str | None:
    head = git_ok(repo, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    if head:
        return head.removeprefix("refs/remotes/")
    for name in ("main", "master", "trunk", "develop"):
        for ref in (name, f"origin/{name}"):
            if commit_sha(repo, ref):
                return ref
    return None


def merge_base(repo: Path, a: str, b: str) -> str | None:
    return git_ok(repo, "merge-base", a, b)


def pathspec(under: str | None = None, extra: tuple[str, ...] = ()) -> list[str]:
    """`-- <under or .> :(exclude)...` — limits a git query and hides the skill's own output."""
    return ["--", under or ".", *(f":(exclude){p}" for p in (*EXCLUDES, *extra))]


def shell_pathspec() -> str:
    return " ".join(shlex.quote(a) for a in pathspec())


def untracked_files(repo: Path, under: str | None = None) -> list[str]:
    rc, out = git(repo, "ls-files", "--others", "--exclude-standard", "-z", *pathspec(under))
    if rc != 0:
        return []
    return sorted(p for p in out.split("\0") if p)


def is_dirty(repo: Path) -> bool:
    rc, out = git(repo, "status", "--porcelain", "--untracked-files=all", *pathspec())
    return rc == 0 and bool(out.strip())


def read_bytes(path: Path) -> bytes:
    try:
        with open(path, "rb") as fh:
            return fh.read(MAX_UNTRACKED_BYTES)
    except OSError:
        return b""


# --------------------------------------------------------------------------- slugs, hashing


def kebab(text: str, maxlen: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:maxlen].rstrip("-") or "target"


def sha1(*chunks: bytes | str) -> str:
    h = hashlib.sha1()
    for chunk in chunks:
        h.update(chunk.encode("utf-8") if isinstance(chunk, str) else chunk)
        h.update(b"\0")
    return h.hexdigest()


# --------------------------------------------------------------------------- change sets


def diff_files(repo: Path, diff_args: list[str]) -> list[dict]:
    _, numstat = git(repo, "diff", "--numstat", "--no-renames", *diff_args, *pathspec())
    _, names = git(repo, "diff", "--name-status", "--no-renames", *diff_args, *pathspec())
    status = {}
    for line in names.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            status[parts[-1]] = parts[0][:1]
    files = []
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        binary = added == "-" or deleted == "-"
        files.append({
            "path": path,
            "status": status.get(path, "M"),
            "added": 0 if binary else int(added),
            "deleted": 0 if binary else int(deleted),
            "binary": binary,
        })
    return files


def untracked_entries(repo: Path, paths: list[str]) -> tuple[list[dict], list[bytes]]:
    entries, contents = [], []
    for rel in paths:
        data = read_bytes(repo / rel)
        binary = b"\0" in data[:8000]
        entries.append({
            "path": rel,
            "status": "?",
            "added": 0 if binary else data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0),
            "deleted": 0,
            "binary": binary,
        })
        contents.append(rel.encode("utf-8") + b"\0" + hashlib.sha1(data).hexdigest().encode())
    return entries, contents


def build_changes(repo: Path, scope: str, ref: str | None, base_arg: str | None) -> tuple[dict, str, list[str]]:
    """Return (changes, fingerprint, notes) for a resolved change scope."""
    notes: list[str] = []
    head_sha = commit_sha(repo, "HEAD")
    include_untracked = False
    branch = None

    if scope == "uncommitted":
        base = head_sha or EMPTY_TREE
        diff_args = [base]
        head = "WORKTREE"
        include_untracked = True
        diff_cmd = "git diff HEAD" if head_sha else f"git diff {EMPTY_TREE}"
        if not head_sha:
            notes.append("repository has no commits yet; diffing against the empty tree")
    elif scope == "staged":
        base = head_sha or EMPTY_TREE
        diff_args = ["--cached", base]
        head = "INDEX"
        diff_cmd = "git diff --cached" + ("" if head_sha else f" {EMPTY_TREE}")
    elif scope == "branch":
        target_ref = ref or "HEAD"
        branch = ref or current_branch(repo)
        against = base_arg or default_base(repo)
        if against is None:
            raise InputError("branch scope needs a base: no origin/HEAD, main, master, trunk or develop found; pass --base <ref>")
        if commit_sha(repo, against) is None:
            raise InputError(f"--base {against!r} does not resolve to a commit")
        base = merge_base(repo, against, target_ref)
        if base is None:
            raise InputError(f"no merge-base between {against!r} and {target_ref!r}")
        if ref is None:
            diff_args = [base]  # includes uncommitted work on the current branch
            dirty = is_dirty(repo)
            head = "WORKTREE" if dirty else (head_sha or "HEAD")
            include_untracked = dirty
            diff_cmd = f"git diff {base}"
        else:
            diff_args = [base, target_ref]
            head = commit_sha(repo, target_ref) or target_ref
            diff_cmd = f"git diff {base} {target_ref}"
        notes.append(f"base is the merge-base of {against} and {target_ref}")
    elif scope == "commit":
        sha = commit_sha(repo, ref or "HEAD")
        if sha is None:
            raise InputError(f"{ref!r} does not resolve to a commit")
        parent = commit_sha(repo, f"{sha}^")
        base = parent or EMPTY_TREE
        if parent is None:
            notes.append("root commit; diffing against the empty tree")
        diff_args = [base, sha]
        head = sha
        diff_cmd = f"git diff {base} {sha}"
    elif scope == "range":
        m = RANGE.match(ref or "")
        if not m:
            raise InputError(f"{ref!r} is not a range")
        a, op, b = m.group("a"), m.group("op"), m.group("b")
        sha_a, sha_b = commit_sha(repo, a), commit_sha(repo, b)
        if not sha_a or not sha_b:
            raise InputError(f"range {ref!r}: both sides must resolve to commits")
        base = merge_base(repo, sha_a, sha_b) if op == "..." else sha_a
        if base is None:
            raise InputError(f"range {ref!r}: no merge-base")
        diff_args = [base, sha_b]
        head = sha_b
        diff_cmd = f"git diff {ref}"
    else:  # pragma: no cover - guarded by callers
        raise InputError(f"unknown scope {scope!r}")

    files = diff_files(repo, diff_args)
    _, raw_diff = git(repo, "diff", "--no-renames", *diff_args, *pathspec())
    diff_cmd = f"{diff_cmd} {shell_pathspec()}"
    extra: list[bytes] = []
    if include_untracked:
        entries, extra = untracked_entries(repo, untracked_files(repo))
        files += entries
        if entries:
            notes.append(f"{len(entries)} untracked file(s) are not in `{diff_cmd}`; read them directly")

    files.sort(key=lambda f: f["path"])
    totals = {
        "files": len(files),
        "added": sum(f["added"] for f in files),
        "deleted": sum(f["deleted"] for f in files),
    }
    if totals["files"] == 0:
        notes.append("empty change set: there is nothing to analyze")

    changes = {
        "scope": scope,
        "base": base,
        "head": head,
        "dirty": is_dirty(repo),
        "diff_cmd": diff_cmd,
        "files": files,
        "totals": totals,
    }
    if branch:
        changes["branch"] = branch
    return changes, sha1(raw_diff, *extra), notes


def changes_slug(scope: str, changes: dict, ref: str | None) -> str:
    if scope in ("uncommitted", "staged"):
        return f"changes-{scope}"
    if scope == "branch":
        return "changes-branch-" + kebab(changes.get("branch") or ref or "head", 40)
    if scope == "commit":
        return f"changes-{changes['head'][:7]}"
    return f"changes-{changes['base'][:7]}-{changes['head'][:7]}"


# --------------------------------------------------------------------------- feature helpers


def symbol_matches(repo: Path, token: str) -> list[str]:
    needle = re.split(r"\.|::|#", token)[-1]
    docs = tuple(f"*{ext}" for ext in sorted(DOC_EXTS))  # a word in a doc is not a built feature
    rc, out = git(repo, "grep", "-n", "-I", "-w", "-F", "-e", needle, *pathspec(extra=docs))
    if rc != 0:
        return []
    return [line.strip()[:160] for line in out.splitlines()[:MAX_MATCHES]]


def path_fingerprint(repo: Path, rel: str, in_git: bool) -> str:
    target = repo / rel
    if in_git:
        _, staged = git(repo, "ls-files", "-s", *pathspec(rel))
        _, worktree = git(repo, "diff", "HEAD", *pathspec(rel)) if commit_sha(repo, "HEAD") else (0, "")
        _, extra = untracked_entries(repo, untracked_files(repo, rel))
        return sha1(rel, staged, worktree, *extra)
    chunks: list[str] = [rel]
    if target.is_file():
        chunks.append(hashlib.sha1(read_bytes(target)).hexdigest())
    else:
        for root, dirs, names in os.walk(target):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in sorted(names):
                p = Path(root) / name
                try:
                    st = p.stat()
                except OSError:
                    continue
                chunks.append(f"{p.relative_to(repo)}:{st.st_size}:{int(st.st_mtime)}")
    return sha1(*chunks)


def find_path(repo: Path, text: str) -> Path | None:
    if not text or "\n" in text:
        return None
    for candidate in (Path(text), repo / text):
        try:
            if candidate.exists():
                return candidate.resolve()
        except OSError:
            continue
    return None


def rel_to(repo: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo.resolve()))
    except ValueError:
        return str(path)


def doc_candidates(repo: Path, limit: int = 5) -> list[dict]:
    found: list[tuple[float, str]] = []
    for top in DOC_DIRS:
        base = repo / top
        if not base.is_dir():
            continue
        for root, dirs, names in os.walk(base):
            depth = len(Path(root).relative_to(base).parts)
            dirs[:] = [] if depth >= 2 else sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in names:
                p = Path(root) / name
                if p.suffix.lower() in DOC_EXTS:
                    try:
                        found.append((p.stat().st_mtime, rel_to(repo, p)))
                    except OSError:
                        continue
    found.sort(key=lambda t: (-t[0], t[1]))
    out = []
    for mtime, rel in found[:limit]:
        day = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")
        out.append({"kind": "plan", "spec": rel, "label": f"{rel} (modified {day})"})
    return out


def commit_candidates(repo: Path, limit: int = 5) -> list[dict]:
    rc, out = git(repo, "log", f"-{limit}", "--format=%h%x09%s")
    if rc != 0:
        return []
    cands = []
    for line in out.splitlines():
        short, _, subject = line.partition("\t")
        cands.append({"kind": "changes", "spec": short, "label": f"{short} {subject}"[:100]})
    return cands


# --------------------------------------------------------------------------- resolution


def result(kind: str, spec: str, slug: str, fingerprint: str, reason: str, **extra) -> dict:
    out = {"kind": kind, "spec": spec, "slug": slug, "fingerprint": fingerprint, "reason": reason}
    # A resolved target always carries `built` (null = not yet known); other extras only when set.
    out.update({k: v for k, v in extra.items() if v is not None or k == "built"})
    out.setdefault("notes", [])
    return out


def resolve_changes(repo: Path, scope: str, ref: str | None, base_arg: str | None, reason: str) -> dict:
    if not is_git_repo(repo):
        raise InputError("a changes target needs a git repository")
    changes, fp, notes = build_changes(repo, scope, ref, base_arg)
    spec = ref if scope in ("commit", "range") or (scope == "branch" and ref) else scope
    return result("changes", spec, changes_slug(scope, changes, ref), fp, reason,
                  built=True, changes=changes, notes=notes)


def resolve_ref_token(repo: Path, token: str, base_arg: str | None, reason_prefix: str | None) -> dict | None:
    """reason_prefix None = auto detection: each outcome names its own rule (7, 9, 10, 11)."""
    """A single token that names a branch, commit, or range → changes; else None."""
    if RANGE.match(token):
        m = RANGE.match(token)
        if commit_sha(repo, m.group("a")) and commit_sha(repo, m.group("b")):
            return resolve_changes(repo, "range", token, base_arg, f"{reason_prefix or 'rule 7'}: {token!r} is a commit range")
        return None
    if commit_sha(repo, token) is None:
        return None
    if is_branch(repo, token):
        if token == current_branch(repo):
            return resolve_changes(repo, "branch", None, base_arg,
                                   f"{reason_prefix or 'rule 9'}: {token!r} is the current branch; analyzing its changes "
                                   "vs base, including uncommitted work")
        return resolve_changes(repo, "branch", token, base_arg,
                               f"{reason_prefix or 'rule 10'}: {token!r} is a branch; analyzing its commits vs its merge-base")
    return resolve_changes(repo, "commit", token, base_arg, f"{reason_prefix or 'rule 11'}: {token!r} resolves to a commit")


def resolve_feature_text(repo: Path, text: str, in_git: bool, reason: str | None) -> dict:
    """reason None = auto detection: a symbol hit is rule 12, a description rule 13."""
    head = commit_sha(repo, "HEAD") if in_git else None
    if IDENT.match(text) and in_git:
        hits = symbol_matches(repo, text)
        if hits:
            return result("feature", text, kebab(text), sha1(text, head or ""),
                          f"{reason or 'rule 12'}: {text!r} is a symbol found in tracked code",
                          built=True, matches=hits)
    words = text.split()
    return result("feature", text, kebab(" ".join(words[:6])), sha1(text, head or ""),
                  f"{reason or 'rule 13'}: a description; pre-flight settles whether it is built",
                  built=None)


def doc_slug(rel: str) -> str:
    """Last two path parts, so docs/a/plan.md and docs/b/plan.md do not share a work dir."""
    return kebab("-".join(Path(rel).with_suffix("").parts[-2:]))


def resolve(target: str | None, kind: str, base_arg: str | None, repo: Path,
            excludes: list[str] | None = None) -> dict:
    global EXCLUDES
    EXCLUDES = list(dict.fromkeys([*DEFAULT_EXCLUDES, *(e.strip("/") for e in excludes or [] if e.strip("/"))]))
    target = (target or "").strip() or None
    repo = repo.resolve()
    in_git = is_git_repo(repo)

    # ---- explicit --target -------------------------------------------------------------
    if kind == "plan":
        path = find_path(repo, target or "")
        if path is None or not path.is_file():
            raise InputError(f"--target plan needs an existing file, got {target!r}")
        rel = rel_to(repo, path)
        return result("plan", rel, doc_slug(rel), sha1(read_bytes(path)), "--target plan", built=None)

    if kind == "changes":
        if target is None:
            return resolve_changes(repo, "uncommitted", None, base_arg, "--target changes with no target: uncommitted")
        if target in SCOPES:
            return resolve_changes(repo, target, None, base_arg, f"--target changes: {target}")
        hit = resolve_ref_token(repo, target, base_arg, "--target changes")
        if hit is None:
            raise InputError(f"{target!r} is not a scope, branch, commit, or range")
        return hit

    if kind == "feature":
        if target is None:
            raise InputError("--target feature needs a path, symbol, or description")
        path = find_path(repo, target)
        if path is not None:
            rel = rel_to(repo, path)
            return result("feature", rel, kebab("-".join(Path(rel).with_suffix("").parts[-2:])),
                          path_fingerprint(repo, rel, in_git), "--target feature: existing path", built=True)
        return resolve_feature_text(repo, target, in_git, "--target feature")

    # ---- auto ----------------------------------------------------------------------------
    if target is None:
        if in_git and is_dirty(repo):
            return resolve_changes(repo, "uncommitted", None, base_arg, "rule 1: no target and the working tree is dirty")
        if in_git and current_branch(repo):
            against = base_arg or default_base(repo)
            head = commit_sha(repo, "HEAD")
            if against and head and commit_sha(repo, against):
                mb = merge_base(repo, against, "HEAD")
                if mb and mb != head:
                    return resolve_changes(repo, "branch", None, base_arg,
                                           f"rule 2: no target and {current_branch(repo)} is ahead of {against}")
        cands = doc_candidates(repo) + (commit_candidates(repo) if in_git else [])
        return result("ask", "", "", "", "rule 3: no target, clean tree, nothing ahead of base",
                      candidates=cands, notes=[] if cands else ["no plan documents or commits found to suggest"])

    if target in SCOPES:
        return resolve_changes(repo, target, None, base_arg, f"rule 4: {target!r} is a change scope")

    path = find_path(repo, target)
    if path is not None:
        rel = rel_to(repo, path)
        if path.is_file() and path.suffix.lower() in DOC_EXTS:
            return result("plan", rel, doc_slug(rel), sha1(read_bytes(path)),
                          f"rule 5: {rel} is a document", built=None)
        return result("feature", rel, kebab("-".join(Path(rel).with_suffix("").parts[-2:])),
                      path_fingerprint(repo, rel, in_git), f"rule 6: {rel} is an existing source path", built=True)

    if in_git and " " not in target:
        if RANGE.match(target):
            hit = resolve_ref_token(repo, target, base_arg, None)
            if hit:
                return hit
        is_ref = commit_sha(repo, target) is not None
        looks_symbolic = IDENT.match(target) and target not in GIT_NAMES and not (is_ref and HEX_SHA.match(target))
        hits = symbol_matches(repo, target) if looks_symbolic else []
        if is_ref and hits:
            return result("ask", target, "", "",
                          f"rule 8: {target!r} is both a git ref and a symbol in tracked code",
                          candidates=[
                              {"kind": "changes", "spec": target, "label": f"the changes in {target}"},
                              {"kind": "feature", "spec": target, "label": f"the code named {target} ({len(hits)} hits)"},
                          ],
                          matches=hits)
        if is_ref:
            hit = resolve_ref_token(repo, target, base_arg, None)
            if hit:
                return hit

    return resolve_feature_text(repo, target, in_git, None)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", nargs="?", help="document path, source path, symbol, description, scope, ref, or range")
    ap.add_argument("--target", dest="kind", default="auto", choices=["auto", "feature", "plan", "changes"])
    ap.add_argument("--base", default=None, help="base ref for branch scope (default: merge-base with the default branch)")
    ap.add_argument("--repo", default=".", help="project directory (default: cwd)")
    ap.add_argument("--exclude", action="append", default=[], metavar="PATH",
                    help="repo-relative path to hide from every git query (repeatable); "
                         ".edge-cases and reviews/edge-cases are always hidden")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"resolve_target: --repo {args.repo!r} is not a directory", file=sys.stderr)
        return 2
    try:
        out = resolve(args.target, args.kind, args.base, repo, args.exclude)
    except InputError as exc:
        print(f"resolve_target: {exc}", file=sys.stderr)
        return 2
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
