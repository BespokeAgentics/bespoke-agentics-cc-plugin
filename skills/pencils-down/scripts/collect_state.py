#!/usr/bin/env python3
"""Collect the evidence the pencils-down skill reasons over, as one JSON document.

Stdlib only. Deterministic. Read-only — never writes inside the repo it inspects.

    python3 collect_state.py --repo . --window 90d --out /tmp/pencils-down-state.json

Sources, each independent and each recorded in `notes` when unavailable:

  repo         identity, default branch, manifest metadata (name/version/description/license/repo)
  commits      commits in the window: sha, date, author, subject, WIP/TODO markers, paths touched
  branches     local branches with last-commit date and staleness in days
  uncommitted  modified / untracked paths in the working tree
  plans        plan-shaped documents (plans/, docs/plans/, ROADMAP*, TODO*, PLAN*, *.plan.md, specs/)
  wiki         wiki/ presence, page count, most recently edited pages
  markers      TODO / FIXME / HACK / XXX / not implemented markers with file:line (capped)
  flags        feature-flag-shaped identifiers with file:line (capped)
  tests        test directories, test files count, test command from the manifest
  ci           CI workflow files
  go_live      inventory of the files a public repository is expected to carry
  env          env vars read by the code vs declared in .env.example

Everything here is a pointer with a rule attached, not a conclusion. The skill reads the real
files for anything it reports on.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", ".venv", "venv", "target", "vendor",
    "__pycache__", ".turbo", ".cache", "coverage", ".pytest_cache", ".mypy_cache", "out",
}
CODE_EXT = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rs", ".rb", ".java", ".kt",
    ".swift", ".cs", ".php", ".vue", ".svelte", ".astro", ".dart", ".ex", ".exs",
}
MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b|not implemented|NotImplemented|unimplemented!", re.I)
FLAG_RE = re.compile(
    r"\b(feature[_-]?flags?|featureFlag|isEnabled|is_enabled|FEATURE_[A-Z0-9_]+|ENABLE_[A-Z0-9_]+|"
    r"flags\.[A-Za-z_]+|useFlag|getFlag|experimental)\b"
)
ENV_RE = re.compile(r"process\.env\.([A-Z][A-Z0-9_]+)|os\.environ(?:\.get)?\(\s*['\"]([A-Z][A-Z0-9_]+)|os\.getenv\(\s*['\"]([A-Z][A-Z0-9_]+)|Deno\.env\.get\(\s*['\"]([A-Z][A-Z0-9_]+)|Bun\.env\.([A-Z][A-Z0-9_]+)")
WIP_RE = re.compile(r"\b(wip|todo|fixme|hack|temp|tmp|stub|placeholder|draft)\b", re.I)
MARKER_CAP = 200
FLAG_CAP = 100


def parse_window(spec: str) -> timedelta:
    m = re.fullmatch(r"(\d+)([dwm])", spec.strip().lower())
    if not m:
        raise SystemExit(f"--window must look like 90d, 12w or 3m; got {spec!r}")
    n, unit = int(m.group(1)), m.group(2)
    return timedelta(days=n * {"d": 1, "w": 7, "m": 30}[unit])


def git(repo: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def walk_files(repo: Path):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if (d not in SKIP_DIRS and not d.startswith(".")) or d in {".github", ".claude"}]
        for f in files:
            yield Path(root) / f


def rel(repo: Path, p: Path) -> str:
    try:
        return str(p.relative_to(repo))
    except ValueError:
        return str(p)


def read_json(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def collect_repo(repo: Path, notes: list[str]) -> dict:
    out: dict = {"path": str(repo), "is_git": False, "manifests": []}
    top = git(repo, "rev-parse", "--show-toplevel")
    if top:
        out["is_git"] = True
        out["toplevel"] = top.strip()
        out["branch"] = (git(repo, "branch", "--show-current") or "").strip() or None
        remote = git(repo, "remote", "get-url", "origin")
        out["origin"] = remote.strip() if remote else None
        shallow = git(repo, "rev-parse", "--is-shallow-repository")
        if shallow and shallow.strip() == "true":
            notes.append("Shallow clone: commit history is truncated; the window may be incomplete.")
        head = git(repo, "rev-list", "--count", "HEAD")
        out["total_commits"] = int(head.strip()) if head and head.strip().isdigit() else None
    else:
        notes.append("Not a git repository: commits, branches and uncommitted work are unavailable.")

    pkg = repo / "package.json"
    if pkg.exists():
        d = read_json(pkg) or {}
        out["manifests"].append({
            "file": "package.json", "name": d.get("name"), "version": d.get("version"),
            "description": d.get("description"), "license": d.get("license"),
            "repository": d.get("repository"), "private": d.get("private"),
            "scripts": sorted((d.get("scripts") or {}).keys()),
        })
    pyp = repo / "pyproject.toml"
    if pyp.exists():
        txt = pyp.read_text(encoding="utf-8", errors="replace")
        def grab(key):
            m = re.search(rf'^{key}\s*=\s*"([^"]*)"', txt, re.M)
            return m.group(1) if m else None
        out["manifests"].append({"file": "pyproject.toml", "name": grab("name"), "version": grab("version"),
                                 "description": grab("description"), "license": grab("license")})
    for name in ("Cargo.toml", "go.mod", "pubspec.yaml", "mix.exs", "Gemfile"):
        if (repo / name).exists():
            out["manifests"].append({"file": name})
    if not out["manifests"]:
        notes.append("No package manifest found: name/version/description must come from the README or the user.")
    return out


def collect_commits(repo: Path, since: datetime, notes: list[str]) -> list[dict]:
    fmt = "%H%x1f%aI%x1f%an%x1f%s%x1e"
    raw = git(repo, "log", f"--since={since.isoformat()}", f"--format={fmt}", "--name-only")
    if raw is None:
        return []
    commits: list[dict] = []
    for block in raw.split("\x1e"):
        block = block.strip("\n")
        if not block.strip():
            continue
        header, _, files = block.partition("\n")
        parts = header.strip().split("\x1f")
        if len(parts) < 4:
            continue
        sha, date, author, subject = parts[:4]
        paths = [p for p in files.strip().split("\n") if p.strip()]
        commits.append({
            "sha": sha[:10], "date": date, "author": author, "subject": subject,
            "wip_marker": bool(WIP_RE.search(subject)),
            "paths": paths[:50], "path_count": len(paths),
        })
    if not commits:
        notes.append("No commits in the window.")
    return commits


def collect_branches(repo: Path, now: datetime) -> list[dict]:
    # for-each-ref does not expand %x1f the way git log does; use a literal separator.
    sep = "|@|"
    raw = git(repo, "for-each-ref", f"--format=%(refname:short){sep}%(committerdate:iso-strict){sep}%(subject)", "refs/heads/")
    if not raw:
        return []
    rows = []
    for line in raw.strip().split("\n"):
        parts = line.split(sep, 2)
        if len(parts) < 3:
            continue
        name, date, subject = parts
        try:
            d = datetime.fromisoformat(date)
            stale = (now - d).days
        except ValueError:
            stale = None
        rows.append({"name": name, "last_commit": date, "stale_days": stale, "subject": subject})
    return sorted(rows, key=lambda r: (r["stale_days"] is None, -(r["stale_days"] or 0)))


def collect_uncommitted(repo: Path) -> dict:
    raw = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    if raw is None:
        return {"modified": [], "untracked": []}
    modified, untracked = [], []
    for line in raw.rstrip("\n").split("\n"):
        if not line.strip():
            continue
        code, path = line[:2], line[3:]
        (untracked if code == "??" else modified).append(path)
    return {"modified": modified[:200], "untracked": untracked[:200],
            "modified_count": len(modified), "untracked_count": len(untracked)}


def collect_plans(repo: Path) -> list[dict]:
    hits: list[dict] = []
    name_re = re.compile(r"^(ROADMAP|TODO|PLAN|BACKLOG|MILESTONES?)[^/]*\.(md|txt)$", re.I)
    for p in walk_files(repo):
        r = rel(repo, p)
        parts = r.split("/")
        in_plan_dir = any(seg in {"plans", "specs", "rfcs", "adr", "adrs"} for seg in parts[:-1]) or "docs/plans" in r
        if (in_plan_dir and p.suffix.lower() in {".md", ".txt"}) or name_re.match(p.name) or p.name.endswith(".plan.md"):
            try:
                st = p.stat()
                head = p.read_text(encoding="utf-8", errors="replace")[:600]
            except OSError:
                continue
            title = next((ln.lstrip("# ").strip() for ln in head.splitlines() if ln.startswith("#")), p.stem)
            hits.append({"path": r, "title": title, "bytes": st.st_size,
                         "modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()})
    return sorted(hits, key=lambda h: h["modified"], reverse=True)[:60]


def collect_wiki(repo: Path, notes: list[str]) -> dict:
    wiki = repo / "wiki"
    if not wiki.is_dir():
        notes.append("No wiki/ vault: project intelligence must come from plans, commits and the user.")
        return {"present": False}
    pages = [p for p in wiki.rglob("*.md") if not p.name.startswith("_")]
    recent = sorted(pages, key=lambda p: p.stat().st_mtime, reverse=True)[:15]
    return {
        "present": True, "page_count": len(pages),
        "has_schema": (wiki / "_schema" / "SCHEMA.md").exists(),
        "has_log": (wiki / "_log.md").exists(),
        "recent_pages": [rel(repo, p) for p in recent],
    }


def scan_code(repo: Path) -> tuple[list[dict], list[dict], dict]:
    markers: list[dict] = []
    flags: list[dict] = []
    env_used: dict[str, str] = {}
    marker_total = flag_total = 0
    for p in walk_files(repo):
        if p.suffix.lower() not in CODE_EXT:
            continue
        try:
            if p.stat().st_size > 1_000_000:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        r = rel(repo, p)
        for i, line in enumerate(text.splitlines(), 1):
            if MARKER_RE.search(line):
                marker_total += 1
                if len(markers) < MARKER_CAP:
                    markers.append({"file": r, "line": i, "text": line.strip()[:160]})
            if FLAG_RE.search(line):
                flag_total += 1
                if len(flags) < FLAG_CAP:
                    flags.append({"file": r, "line": i, "text": line.strip()[:160]})
            for m in ENV_RE.finditer(line):
                name = next(g for g in m.groups() if g)
                env_used.setdefault(name, f"{r}:{i}")
    return (
        markers, flags,
        {"markers_total": marker_total, "markers_capped": marker_total > MARKER_CAP,
         "flags_total": flag_total, "flags_capped": flag_total > FLAG_CAP, "env_used": env_used},
    )


def collect_tests(repo: Path, manifests: list[dict], notes: list[str]) -> dict:
    test_files = 0
    test_dirs: set[str] = set()
    test_re = re.compile(r"(\.|_)(test|spec)\.[a-z]+$|^test_.*\.py$|_test\.(go|rs)$")
    for p in walk_files(repo):
        if test_re.search(p.name) or any(seg in {"tests", "test", "__tests__", "spec", "e2e"} for seg in rel(repo, p).split("/")[:-1]):
            if p.suffix.lower() in CODE_EXT:
                test_files += 1
                test_dirs.add(rel(repo, p.parent).split("/")[0])
    cmd = None
    for m in manifests:
        if m.get("file") == "package.json" and "test" in (m.get("scripts") or []):
            cmd = "npm test (or bun/pnpm test)"
    if cmd is None and (repo / "pyproject.toml").exists():
        cmd = "pytest (assumed; confirm in pyproject)"
    if cmd is None and (repo / "go.mod").exists():
        cmd = "go test ./..."
    if cmd is None and (repo / "Cargo.toml").exists():
        cmd = "cargo test"
    if test_files == 0:
        notes.append("No test files found: 'tests green' cannot be a go-live gate until some exist.")
    return {"test_files": test_files, "test_roots": sorted(test_dirs), "test_command": cmd}


def collect_ci(repo: Path) -> list[str]:
    found = []
    wf = repo / ".github" / "workflows"
    if wf.is_dir():
        found += [rel(repo, p) for p in sorted(wf.iterdir()) if p.suffix in {".yml", ".yaml"}]
    for name in (".gitlab-ci.yml", ".circleci/config.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml", "Jenkinsfile"):
        if (repo / name).exists():
            found.append(name)
    return found


def collect_go_live(repo: Path, env_used: dict[str, str]) -> dict:
    def first(*globs: str) -> str | None:
        for g in globs:
            hits = sorted(repo.glob(g))
            if hits:
                return rel(repo, hits[0])
        return None

    inventory = {
        "readme": first("README*", "readme*"),
        "license": first("LICENSE*", "LICENCE*", "COPYING*"),
        "contributing": first("CONTRIBUTING*", ".github/CONTRIBUTING*"),
        "changelog": first("CHANGELOG*", "HISTORY*", "RELEASES*"),
        "security": first("SECURITY*", ".github/SECURITY*"),
        "code_of_conduct": first("CODE_OF_CONDUCT*", ".github/CODE_OF_CONDUCT*"),
        "issue_templates": first(".github/ISSUE_TEMPLATE/*", ".github/ISSUE_TEMPLATE*"),
        "pr_template": first(".github/PULL_REQUEST_TEMPLATE*", ".github/pull_request_template*"),
        "env_example": first(".env.example", ".env.sample", ".env.template"),
        "dockerfile": first("Dockerfile", "docker-compose.y*ml", "compose.y*ml"),
        "release_config": first(".releaserc*", "release.config.*", ".changeset", "cliff.toml", ".github/workflows/release*"),
        "funding": first(".github/FUNDING.yml"),
        "docs_dir": first("docs"),
    }
    readme = inventory["readme"]
    readme_info = None
    if readme:
        try:
            txt = (repo / readme).read_text(encoding="utf-8", errors="replace")
            headings = [ln.strip() for ln in txt.splitlines() if ln.startswith("#")][:40]
            readme_info = {
                "bytes": len(txt), "headings": headings,
                "mentions_install": bool(re.search(r"\binstall", txt, re.I)),
                "mentions_quickstart": bool(re.search(r"quick ?start|getting started|usage", txt, re.I)),
                "mentions_license": bool(re.search(r"\blicen[cs]e\b", txt, re.I)),
                "has_images": bool(re.search(r"!\[[^\]]*\]\(", txt)),
                "placeholder_text": bool(re.search(r"lorem ipsum|TODO|TBD|coming soon", txt)),
            }
        except OSError:
            pass

    env_declared: list[str] = []
    if inventory["env_example"]:
        try:
            for ln in (repo / inventory["env_example"]).read_text(encoding="utf-8", errors="replace").splitlines():
                m = re.match(r"\s*(?:export\s+)?([A-Z][A-Z0-9_]+)\s*=", ln)
                if m:
                    env_declared.append(m.group(1))
        except OSError:
            pass
    undeclared = sorted(set(env_used) - set(env_declared))
    unused = sorted(set(env_declared) - set(env_used))
    return {
        "inventory": inventory, "readme": readme_info,
        "env": {"used_in_code": sorted(env_used), "declared_in_example": env_declared,
                "used_but_undeclared": undeclared, "declared_but_unused": unused},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="repository root (default: cwd)")
    ap.add_argument("--window", default="90d", help="how far back to read commits: 90d, 12w, 3m")
    ap.add_argument("--out", help="write JSON here (default: stdout)")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"not a directory: {repo}", file=sys.stderr)
        return 2
    now = datetime.now(timezone.utc)
    since = now - parse_window(args.window)
    notes: list[str] = []

    repo_info = collect_repo(repo, notes)
    commits = collect_commits(repo, since, notes) if repo_info["is_git"] else []
    branches = collect_branches(repo, now) if repo_info["is_git"] else []
    uncommitted = collect_uncommitted(repo) if repo_info["is_git"] else {"modified": [], "untracked": []}
    plans = collect_plans(repo)
    if not plans:
        notes.append("No plan-shaped documents found: intent must come from commits, the README and the user.")
    wiki = collect_wiki(repo, notes)
    markers, flags, scan = scan_code(repo)
    if scan["markers_capped"]:
        notes.append(f"Markers capped at {MARKER_CAP} of {scan['markers_total']}; grep for the rest.")
    tests = collect_tests(repo, repo_info["manifests"], notes)
    ci = collect_ci(repo)
    if not ci:
        notes.append("No CI configuration found: 'CI green' is not available as a go-live gate.")
    go_live = collect_go_live(repo, scan["env_used"])
    if go_live["env"]["used_but_undeclared"]:
        notes.append(f"{len(go_live['env']['used_but_undeclared'])} env var(s) read by code are missing from the env example.")

    doc = {
        "generated_at": now.isoformat(),
        "window": {"spec": args.window, "since": since.isoformat()},
        "repo": repo_info,
        "commits": commits,
        "branches": branches,
        "uncommitted": uncommitted,
        "plans": plans,
        "wiki": wiki,
        "markers": markers,
        "flags": flags,
        "tests": tests,
        "ci": ci,
        "go_live": go_live,
        "totals": {
            "commits_in_window": len(commits),
            "wip_commits": sum(1 for c in commits if c["wip_marker"]),
            "markers": scan["markers_total"],
            "flag_sites": scan["flags_total"],
            "branches": len(branches),
            "stale_branches_30d": sum(1 for b in branches if (b["stale_days"] or 0) > 30),
        },
        "notes": notes,
    }
    text = json.dumps(doc, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(text)} bytes; {len(notes)} note(s))", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
