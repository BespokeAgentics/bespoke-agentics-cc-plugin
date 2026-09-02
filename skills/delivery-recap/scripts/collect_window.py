#!/usr/bin/env python3
"""Collect every piece of raw evidence about what was delivered in a time window.

This is the mechanical half of the delivery-recap skill. It does no interpretation:
it gathers commits, working-tree changes, Claude Code session transcripts, and wiki
edits that fall inside the window, and emits one JSON document. Deciding what any of
it *means* for a reader is the model's job, and is deliberately not attempted here.

Stdlib only. Safe to run in a non-git directory (it says so and continues).

Usage:
    python3 collect_window.py --since 24h
    python3 collect_window.py --since "2026-08-28" --until "2026-08-30" --out window.json
    python3 collect_window.py --since 3d --author me --repo /path/to/repo

Output: JSON on stdout (or --out FILE). Read the `notes` array first — it records
everything that was unavailable, so the report can be honest about its blind spots.
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

# --------------------------------------------------------------------------- #
# Path classification
#
# These buckets are HINTS for the model, not verdicts. Each carries the rule that
# fired so the model can see why and overrule it after reading the actual diff.
# A path-based guess is right most of the time and wrong in exactly the cases that
# matter most (a "component" that is really a data layer, a "util" that is really
# the pricing engine), which is why the rule travels with the answer.
# --------------------------------------------------------------------------- #

BUCKET_RULES: list[tuple[str, str, str]] = [
    # (bucket, regex, human-readable rule)
    ("test", r"(^|/)(tests?|__tests__|spec|e2e|cypress)/|\.(test|spec)\.[jt]sx?$|_test\.(py|go)$|test_.*\.py$",
     "path is in a test directory or matches a test filename convention"),
    ("db", r"(^|/)(migrations?|migrate|alembic|prisma|schema)/|\.(sql|prisma)$|(^|/)schema\.(rb|py|ts)$|(^|/)models?/",
     "path is a migration, schema, or model definition"),
    ("api", r"(^|/)(api|routes?|controllers?|handlers?|endpoints?|resolvers?|graphql)/|(^|/)route\.[jt]s$|(^|/)server/|\.(proto)$",
     "path is an HTTP/RPC/GraphQL surface"),
    ("service", r"(^|/)(services?|domain|usecases?|lib|core|jobs?|workers?|queues?|tasks?)/",
     "path is application/domain logic"),
    ("ui", r"(^|/)(components?|pages?|views?|screens?|app|ui|features?|containers?|widgets?)/|\.(tsx|jsx|vue|svelte)$|\.(css|scss|sass|less)$|\.(html|hbs|ejs|erb|blade\.php)$",
     "path renders or styles an interface"),
    ("config", r"(^|/)(config|configs|settings|infra|terraform|k8s|helm|deploy|\.github)/|(^|/)(dockerfile|docker-compose[^/]*|makefile|.*\.ya?ml|.*\.toml|.*\.ini|\.env[^/]*)$",
     "path is configuration, infrastructure, or CI"),
    ("docs", r"(^|/)(docs?|wiki|adr)/|\.(md|mdx|rst|txt)$",
     "path is documentation"),
    ("deps", r"(^|/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lock[bx]?|requirements[^/]*\.txt|poetry\.lock|Cargo\.lock|go\.sum|Gemfile\.lock|composer\.lock)$",
     "path is a dependency manifest or lockfile"),
]

NOISE_RE = re.compile(
    r"(^|/)(node_modules|\.git|dist|build|out|coverage|\.next|\.nuxt|__pycache__|\.venv|venv|target|vendor)/"
)


def classify(path: str) -> dict:
    """Return a bucket hint plus the rule that produced it."""
    p = path.lower()
    for bucket, pattern, rule in BUCKET_RULES:
        if re.search(pattern, p):
            return {"bucket_hint": bucket, "rule": rule}
    return {"bucket_hint": "other", "rule": "no path rule matched — read the diff"}


# --------------------------------------------------------------------------- #
# Window parsing
# --------------------------------------------------------------------------- #

RELATIVE_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|d|day|days|w|week|weeks|m|min|mins|minutes)$", re.I)

UNIT_SECONDS = {
    "m": 60, "min": 60, "mins": 60, "minutes": 60,
    "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
    "d": 86400, "day": 86400, "days": 86400,
    "w": 604800, "week": 604800, "weeks": 604800,
}

NAMED_WINDOWS = {
    "today": "since midnight local time",
    "yesterday": "the previous 24 hours",
    "week": "7 days",
    "this-week": "7 days",
    "sprint": "14 days",
}


def parse_since(spec: str, now: datetime) -> tuple[datetime, str]:
    """Resolve a window spec to an absolute start time plus a human label.

    Accepts: '24h', '3d', '2w', '90m', 'today', 'yesterday', 'week', 'sprint',
    or an ISO-ish absolute date/datetime.
    """
    s = spec.strip().lower()

    if s == "today":
        start = now.astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
        return start, "since midnight today"
    if s == "yesterday":
        return now - timedelta(days=1), "the last 24 hours (yesterday onward)"
    if s in ("week", "this-week"):
        return now - timedelta(days=7), "the last 7 days"
    if s == "sprint":
        return now - timedelta(days=14), "the last 14 days"

    m = RELATIVE_RE.match(s)
    if m:
        qty, unit = float(m.group(1)), m.group(2).lower()
        secs = qty * UNIT_SECONDS[unit]
        return now - timedelta(seconds=secs), f"the last {m.group(1)} {m.group(2)}"

    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(spec.strip(), fmt)
            return dt.replace(tzinfo=now.astimezone().tzinfo), f"since {spec.strip()}"
        except ValueError:
            continue

    raise SystemExit(
        f"Could not parse --since '{spec}'. Use forms like 24h, 3d, 2w, today, "
        f"yesterday, week, sprint, or an absolute date like 2026-08-28."
    )


# --------------------------------------------------------------------------- #
# Git
# --------------------------------------------------------------------------- #

def git(repo: Path, *args: str, check: bool = False) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        if check:
            raise
        return ""
    if r.returncode != 0 and check:
        raise RuntimeError(r.stderr.strip())
    return r.stdout


def normalize_remote(url: str) -> str:
    """Turn a git remote into a browsable https base, best effort."""
    url = url.strip()
    if not url:
        return ""
    m = re.match(r"^(?:ssh://)?git@([^:/]+)[:/](.+?)(?:\.git)?/?$", url)
    if m:
        return f"https://{m.group(1)}/{m.group(2)}"
    return re.sub(r"\.git/?$", "", url)


def parse_numstat(text: str) -> list[dict]:
    """Parse `--numstat` output into file records, handling renames and binaries."""
    files = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted, path = parts[0], parts[1], "\t".join(parts[2:])
        binary = added == "-" or deleted == "-"
        renamed_from = None
        # Rename forms: "old => new" or "dir/{old => new}/file"
        if " => " in path:
            brace = re.match(r"^(.*)\{(.*) => (.*)\}(.*)$", path)
            if brace:
                pre, old, new, post = brace.groups()
                renamed_from = f"{pre}{old}{post}".replace("//", "/")
                path = f"{pre}{new}{post}".replace("//", "/")
            else:
                old, new = path.split(" => ", 1)
                renamed_from, path = old, new
        if NOISE_RE.search("/" + path):
            continue
        rec = {
            "path": path,
            "added": None if binary else int(added),
            "deleted": None if binary else int(deleted),
            "binary": binary,
        }
        if renamed_from:
            rec["renamed_from"] = renamed_from
        rec.update(classify(path))
        files.append(rec)
    return files


def collect_commits(repo: Path, since: datetime, until: datetime | None,
                    author: str | None, notes: list[str]) -> list[dict]:
    US, RS = "\x1f", "\x1e"
    fmt = US.join(["%H", "%h", "%an", "%ae", "%aI", "%s", "%b"]) + RS
    args = ["log", f"--since={since.isoformat()}", f"--pretty=format:{fmt}", "--no-merges"]
    if until:
        args.append(f"--until={until.isoformat()}")
    if author:
        args.append(f"--author={author}")
    raw = git(repo, *args)
    if not raw.strip():
        return []

    commits = []
    for chunk in raw.split(RS):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        parts = chunk.split(US)
        if len(parts) < 7:
            continue
        sha, short, an, ae, adate, subject, body = parts[:7]
        files = parse_numstat(git(repo, "show", "--numstat", "--format=", sha))
        commits.append({
            "sha": sha,
            "short": short,
            "author_name": an,
            "author_email": ae,
            "date": adate,
            "subject": subject,
            "body": body.strip(),
            "files": files,
            "insertions": sum(f["added"] or 0 for f in files),
            "deletions": sum(f["deleted"] or 0 for f in files),
        })

    # Merges are excluded above so file attribution stays unambiguous; say so.
    merges = git(repo, "log", f"--since={since.isoformat()}", "--merges", "--oneline").strip()
    if merges:
        notes.append(
            f"{len(merges.splitlines())} merge commit(s) in the window were excluded from "
            f"per-file attribution (their content appears via the merged commits)."
        )
    return commits


def collect_uncommitted(repo: Path) -> dict:
    porcelain = git(repo, "status", "--porcelain=v1")
    staged, unstaged, untracked = [], [], []
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        x, y, path = line[0], line[1], line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip('"')
        if NOISE_RE.search("/" + path):
            continue
        if x == "?" and y == "?":
            untracked.append(path)
            continue
        if x != " ":
            staged.append(path)
        if y != " ":
            unstaged.append(path)

    staged_files = parse_numstat(git(repo, "diff", "--cached", "--numstat"))
    unstaged_files = parse_numstat(git(repo, "diff", "--numstat"))
    return {
        "staged": staged_files,
        "unstaged": unstaged_files,
        "untracked": [dict(path=p, **classify(p)) for p in untracked],
        "has_changes": bool(staged_files or unstaged_files or untracked),
        "summary": {
            "staged_count": len(staged_files),
            "unstaged_count": len(unstaged_files),
            "untracked_count": len(untracked),
        },
        "_status_lines": {"staged": staged, "unstaged": unstaged},
    }


# --------------------------------------------------------------------------- #
# Claude Code session transcripts
# --------------------------------------------------------------------------- #

def encode_project_dir(path: Path) -> str:
    """Claude Code encodes a cwd into a project dir name by replacing / and . with -."""
    return re.sub(r"[/.]", "-", str(path))


def _text_of(content) -> str:
    """Flatten a message content field (string or block list) to plain text.

    Tool results are excluded: they are output the model already saw, not things
    the user said, and they dominate a transcript by volume if left in.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                out.append(b.get("text", ""))
        return "\n".join(out)
    return ""


SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
TAGGED_NOISE = (
    "<local-command-stdout>", "<local-command-caveat>", "<task-notification>",
    "<bash-stdout>", "<bash-stderr>", "<user-prompt-submit-hook>",
)


def extract_prompt(text: str) -> dict | None:
    """Turn one raw user-turn payload into a prompt record, or None if it is noise.

    Two forms carry real intent: what the user typed, and what slash command they
    ran with what arguments. Everything else in a `user` turn — command echo,
    hook output, task notifications, injected reminders — is machinery, and
    reporting it back as if the user said it would be actively misleading.
    """
    text = SYSTEM_REMINDER_RE.sub("", text).strip()
    if not text:
        return None

    if text.startswith(TAGGED_NOISE):
        return None

    if "<command-name>" in text:
        name = re.search(r"<command-name>(.*?)</command-name>", text, re.S)
        argm = re.search(r"<command-args>(.*?)</command-args>", text, re.S)
        cmd = (name.group(1).strip() if name else "").strip()
        cargs = (argm.group(1).strip() if argm else "")
        if not cmd or cmd in ("/model", "/clear", "/compact", "/config", "/cost"):
            return None  # session housekeeping, not delivery intent
        return {
            "kind": "slash-command",
            "text": (f"{cmd} {cargs}".strip())[:4000],
            "command": cmd,
            "args": cargs[:4000],
        }

    if text.startswith("<"):
        return None
    if text.startswith("[Request interrupted") or text.startswith("[Tool use was rejected"):
        return None
    if text.strip() in ("/compact", "/clear", "/model", "/cost", "/config", "/resume"):
        return None
    if len(text) < 3:
        return None
    return {"kind": "typed", "text": text[:4000]}


def _in_window(ts: str, since: datetime, until: datetime | None) -> bool:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if dt < since:
        return False
    if until and dt > until:
        return False
    return True


def collect_sessions(repo: Path, since: datetime, until: datetime | None,
                     scope: str, current_session: str | None,
                     notes: list[str]) -> list[dict]:
    """Mine Claude Code transcripts for what was attempted in the window.

    Transcripts are the only source that records *intent* — the user's own words
    about what they were trying to do. Commits record the result; prompts record
    the goal, which is usually the sentence a reader actually wants.
    """
    if scope == "none":
        return []

    base = Path(os.path.expanduser("~/.claude/projects"))
    if not base.is_dir():
        notes.append("No ~/.claude/projects directory — session transcripts unavailable.")
        return []

    encoded = encode_project_dir(repo)
    candidates = [d for d in base.iterdir() if d.is_dir() and d.name.startswith(encoded)]
    if not candidates:
        notes.append(f"No transcript directory matching this repo ({encoded}).")
        return []

    since_epoch = since.timestamp()
    files = [f for d in candidates for f in d.glob("*.jsonl")]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Claude Code does not reliably export the running session's id, so when it was
    # not passed in, the newest transcript is the best available guess. It is labelled
    # as a guess rather than asserted, because "this is what you did in this session"
    # is exactly the kind of claim that must not be quietly wrong.
    inferred = files[0].stem if files else None
    resolved = current_session or inferred
    id_source = "provided" if current_session else ("inferred-newest-transcript" if inferred else "unknown")

    if scope == "current" and not current_session:
        notes.append(
            f"Session id was not supplied; treating the most recently written transcript "
            f"({inferred}) as the current session. Pass --session-id to be certain."
        )

    sessions = []
    for f in files:
        if f.stat().st_mtime < since_epoch:
            continue  # nothing in this file can fall inside the window
        sid = f.stem
        if scope == "current" and resolved and sid != resolved:
            continue
        rec = mine_session(f, since, until)
        if rec and (rec["user_prompts"] or rec["files_touched"]):
            rec["is_current_session"] = bool(resolved and sid == resolved)
            rec["session_id_source"] = id_source if rec["is_current_session"] else "n/a"
            sessions.append(rec)

    if scope == "current" and not sessions:
        notes.append(
            "The current session's transcript had no in-window activity on disk yet "
            "(entries are flushed as the session proceeds)."
        )
    sessions.sort(key=lambda s: s.get("started") or "", reverse=True)
    return sessions


EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}


def mine_session(path: Path, since: datetime, until: datetime | None) -> dict | None:
    prompts, files_touched, commands, skills = [], {}, [], set()
    started = ended = None
    session_id = path.stem
    cwd = None

    try:
        fh = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return None

    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue

            cwd = cwd or d.get("cwd")
            ts = d.get("timestamp")
            typ = d.get("type")

            if typ not in ("user", "assistant") or not ts:
                continue
            if d.get("isSidechain"):
                continue  # subagent chatter, not the user's thread
            if not _in_window(ts, since, until):
                continue

            started = ts if started is None or ts < started else started
            ended = ts if ended is None or ts > ended else ended

            msg = d.get("message") or {}
            if typ == "user" and not d.get("isMeta"):
                rec = extract_prompt(_text_of(msg.get("content")))
                if rec:
                    prompts.append({"ts": ts, **rec})
            elif typ == "assistant":
                if d.get("attributionSkill"):
                    skills.add(d["attributionSkill"])
                content = msg.get("content")
                if isinstance(content, list):
                    for b in content:
                        if not isinstance(b, dict) or b.get("type") != "tool_use":
                            continue
                        name, inp = b.get("name"), b.get("input") or {}
                        if name in EDIT_TOOLS and isinstance(inp.get("file_path"), str):
                            fp = inp["file_path"]
                            files_touched[fp] = files_touched.get(fp, 0) + 1
                        elif name == "Bash" and isinstance(inp.get("command"), str):
                            commands.append(inp["command"][:400])

    if started is None:
        return None

    return {
        "session_id": session_id,
        "cwd": cwd,
        "transcript": str(path),
        "started": started,
        "ended": ended,
        "user_prompts": prompts,
        "files_touched": [
            dict(path=p, edits=n, **classify(p))
            for p, n in sorted(files_touched.items(), key=lambda kv: -kv[1])
            if not NOISE_RE.search("/" + p)
        ],
        "commands_run": commands[-60:],
        "skills_used": sorted(skills),
    }


# --------------------------------------------------------------------------- #
# Wiki
# --------------------------------------------------------------------------- #

def collect_wiki(repo: Path, wiki_dir: str, since: datetime, until: datetime | None) -> dict:
    wiki = repo / wiki_dir
    if not wiki.is_dir():
        return {"present": False, "dir": wiki_dir, "pages": []}

    pages: dict[str, dict] = {}
    since_epoch = since.timestamp()
    until_epoch = until.timestamp() if until else None

    # Untracked / uncommitted edits show up by mtime; committed ones by git log.
    for p in wiki.rglob("*.md"):
        try:
            mt = p.stat().st_mtime
        except OSError:
            continue
        if mt < since_epoch or (until_epoch and mt > until_epoch):
            continue
        rel = str(p.relative_to(repo))
        pages[rel] = {
            "path": rel,
            "modified": datetime.fromtimestamp(mt, tz=timezone.utc).isoformat(),
            "source": "filesystem mtime",
        }

    log = git(repo, "log", f"--since={since.isoformat()}",
              *( [f"--until={until.isoformat()}"] if until else [] ),
              "--name-only", "--pretty=format:%x1e%h%x1f%aI%x1f%s", "--", wiki_dir)
    for chunk in log.split("\x1e"):
        if not chunk.strip():
            continue
        head, *paths = chunk.strip().splitlines()
        parts = head.split("\x1f")
        if len(parts) < 3:
            continue
        short, adate, subject = parts[:3]
        for rel in paths:
            rel = rel.strip()
            if not rel:
                continue
            entry = pages.setdefault(rel, {"path": rel})
            entry.update({"commit": short, "modified": adate, "subject": subject,
                          "source": "git history"})

    return {
        "present": True,
        "dir": wiki_dir,
        "pages": sorted(pages.values(), key=lambda x: x.get("modified") or "", reverse=True),
        "log_tail": tail_file(wiki / "_log.md", 40),
    }


def tail_file(p: Path, n: int) -> list[str]:
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except OSError:
        return []


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #

def build_file_index(commits, uncommitted, sessions) -> list[dict]:
    """One row per changed path, with where the evidence for it came from."""
    idx: dict[str, dict] = {}

    def touch(path, source, added=0, deleted=0, sha=None):
        e = idx.setdefault(path, {
            "path": path, "added": 0, "deleted": 0,
            "sources": [], "commits": [], **classify(path),
        })
        e["added"] += added or 0
        e["deleted"] += deleted or 0
        if source not in e["sources"]:
            e["sources"].append(source)
        if sha and sha not in e["commits"]:
            e["commits"].append(sha)

    for c in commits:
        for f in c["files"]:
            touch(f["path"], "commit", f.get("added"), f.get("deleted"), c["short"])
    for f in uncommitted.get("staged", []):
        touch(f["path"], "staged", f.get("added"), f.get("deleted"))
    for f in uncommitted.get("unstaged", []):
        touch(f["path"], "unstaged", f.get("added"), f.get("deleted"))
    for f in uncommitted.get("untracked", []):
        touch(f["path"], "untracked")
    for s in sessions:
        for f in s.get("files_touched", []):
            touch(f["path"].replace(str(Path.cwd()) + "/", ""), "session-edit")

    rows = sorted(idx.values(), key=lambda r: -(r["added"] + r["deleted"]))
    return rows


def totals_block(commits, rows, sessions, wiki) -> dict:
    """Counts, split by whether the work is actually on the branch.

    Committed and uncommitted work must never be added into one number. A reader
    told "78 files changed" assumes 78 files shipped; if 41 of those are sitting
    dirty in one working tree, the report has stated a confident falsehood in its
    very first line. So the split is structural here rather than left to whoever
    writes the summary to remember.
    """
    committed_paths, ins, dels = set(), 0, 0
    for c in commits:
        for f in c["files"]:
            committed_paths.add(f["path"])
            ins += f.get("added") or 0
            dels += f.get("deleted") or 0

    uncommitted_only = [r for r in rows if "commit" not in r["sources"]]
    return {
        "commits": len(commits),
        "committed": {
            "files_changed": len(committed_paths),
            "insertions": ins,
            "deletions": dels,
        },
        "uncommitted_or_session_only": {
            "files_changed": len(uncommitted_only),
            "insertions": sum(r["added"] for r in uncommitted_only),
            "deletions": sum(r["deleted"] for r in uncommitted_only),
        },
        "all_touched_files": len(rows),
        "sessions": len(sessions),
        "wiki_pages_touched": len(wiki.get("pages", [])),
        "_note": (
            "Report `committed` as what shipped. `uncommitted_or_session_only` is work that "
            "exists on one machine and is not on the branch — never merge the two into a "
            "single headline figure."
        ),
    }


def bucket_summary(rows: list[dict]) -> dict:
    out: dict[str, dict] = {}
    for r in rows:
        b = out.setdefault(r["bucket_hint"], {"files": 0, "added": 0, "deleted": 0, "examples": []})
        b["files"] += 1
        b["added"] += r["added"]
        b["deleted"] += r["deleted"]
        if len(b["examples"]) < 8:
            b["examples"].append(r["path"])
    return out


def detect_stack(repo: Path) -> dict:
    """Cheap signals so the model knows what kind of app it is reading."""
    marks = {}
    checks = {
        "package.json": "node",
        "pyproject.toml": "python",
        "requirements.txt": "python",
        "go.mod": "go",
        "Cargo.toml": "rust",
        "Gemfile": "ruby",
        "composer.json": "php",
        "next.config.js": "nextjs",
        "next.config.ts": "nextjs",
        "next.config.mjs": "nextjs",
        "vite.config.ts": "vite",
        "nuxt.config.ts": "nuxt",
        "prisma/schema.prisma": "prisma",
        "docker-compose.yml": "docker-compose",
        "wrangler.toml": "cloudflare-workers",
        "wrangler.jsonc": "cloudflare-workers",
    }
    for rel, tag in checks.items():
        if (repo / rel).exists():
            marks[tag] = rel
    pkg = repo / "package.json"
    scripts, deps = {}, []
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8", errors="replace"))
            scripts = data.get("scripts", {}) or {}
            deps = sorted(set(list((data.get("dependencies") or {}).keys())
                              + list((data.get("devDependencies") or {}).keys())))
        except (json.JSONDecodeError, OSError):
            pass
    return {"markers": marks, "package_scripts": scripts, "dependencies": deps[:120]}


def find_url_candidates(repo: Path) -> list[dict]:
    """Grep the obvious places an app's base URL is written down.

    The report is useless if the reader cannot open the thing, so surfacing every
    plausible URL — and letting the model confirm one with the user rather than
    guessing — is worth this scan.
    """
    hits = []
    targets = [
        "README.md", "readme.md", ".env.example", ".env.sample", ".env.local.example",
        "vercel.json", "netlify.toml", "wrangler.toml", "wrangler.jsonc",
        "docker-compose.yml", "docker-compose.yaml", "package.json",
    ]
    url_re = re.compile(r"https?://[^\s\"'`,)\]}>]+|localhost:\d+|127\.0\.0\.1:\d+")
    for rel in targets:
        p = repo / rel
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")[:200_000]
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for m in url_re.findall(line):
                if any(x in m for x in ("schema.org", "w3.org", "example.com", "npmjs",
                                        "github.com", "opensource.org", "json-schema.org")):
                    continue
                hits.append({"file": rel, "line": i, "url": m.rstrip(".,;"),
                             "context": line.strip()[:160]})
    # de-dup by url, keep first sighting
    seen, out = set(), []
    for h in hits:
        if h["url"] in seen:
            continue
        seen.add(h["url"])
        out.append(h)
    return out[:40]


# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description="Collect delivery evidence for a time window.")
    ap.add_argument("--since", default="24h",
                    help="Window start: 24h, 3d, 2w, today, yesterday, week, sprint, or a date.")
    ap.add_argument("--until", default=None, help="Optional window end (date or datetime).")
    ap.add_argument("--repo", default=".", help="Repo root (default: cwd).")
    ap.add_argument("--author", default=None,
                    help="Filter commits by author (git --author pattern). 'me' uses git config user.email.")
    ap.add_argument("--sessions", choices=["current", "all", "none"], default="all",
                    help="Which Claude Code transcripts to mine (default: all in window).")
    ap.add_argument("--session-id", default=os.environ.get("CLAUDE_SESSION_ID"),
                    help="Current session id, so it can be marked in the output.")
    ap.add_argument("--wiki-dir", default="wiki", help="Wiki directory relative to repo root.")
    ap.add_argument("--out", default=None, help="Write JSON here instead of stdout.")
    args = ap.parse_args()

    notes: list[str] = []
    now = datetime.now(timezone.utc)
    since, label = parse_since(args.since, now)
    until, _ = parse_since(args.until, now) if args.until else (None, "")

    repo_arg = Path(args.repo).expanduser().resolve()
    toplevel = git(repo_arg, "rev-parse", "--show-toplevel").strip()
    is_git = bool(toplevel)
    repo = Path(toplevel) if is_git else repo_arg
    if not is_git:
        notes.append(f"{repo} is not a git repository — commit and working-tree evidence unavailable.")

    author = args.author
    if author == "me" and is_git:
        author = git(repo, "config", "--get", "user.email").strip() or None
        if not author:
            notes.append("--author me requested but git config user.email is unset; showing all authors.")

    commits = collect_commits(repo, since, until, author, notes) if is_git else []
    uncommitted = collect_uncommitted(repo) if is_git else {
        "staged": [], "unstaged": [], "untracked": [], "has_changes": False,
        "summary": {"staged_count": 0, "unstaged_count": 0, "untracked_count": 0}}
    sessions = collect_sessions(repo, since, until, args.sessions, args.session_id, notes)
    wiki = collect_wiki(repo, args.wiki_dir, since, until) if is_git or (repo / args.wiki_dir).is_dir() else {
        "present": False, "dir": args.wiki_dir, "pages": []}

    rows = build_file_index(commits, uncommitted, sessions)

    if not commits and not uncommitted.get("has_changes") and not sessions:
        notes.append(
            "No commits, working-tree changes, or session activity found in this window. "
            "Widen the window (--since) or confirm the branch before reporting 'nothing shipped'."
        )

    payload = {
        "generated_at": now.isoformat(),
        "window": {
            "since": since.isoformat(),
            "until": until.isoformat() if until else now.isoformat(),
            "spec": args.since,
            "label": label,
            "author_filter": author,
        },
        "repo": {
            "root": str(repo),
            "is_git": is_git,
            "branch": git(repo, "branch", "--show-current").strip() if is_git else None,
            "head": git(repo, "rev-parse", "--short", "HEAD").strip() if is_git else None,
            "remote": normalize_remote(git(repo, "config", "--get", "remote.origin.url")) if is_git else "",
            "default_branch": (git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
                               .strip().split("/")[-1] or None) if is_git else None,
        },
        "stack": detect_stack(repo),
        "url_candidates": find_url_candidates(repo),
        "commits": commits,
        "uncommitted": uncommitted,
        "sessions": sessions,
        "wiki": wiki,
        "file_index": rows,
        "bucket_summary": bucket_summary(rows),
        "totals": totals_block(commits, rows, sessions, wiki),
        "notes": notes,
    }

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).expanduser().parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).expanduser().write_text(text, encoding="utf-8")
        tot = payload["totals"]
        print(f"Wrote {args.out} — {tot['commits']} commits "
              f"({tot['committed']['files_changed']} files committed, "
              f"{tot['uncommitted_or_session_only']['files_changed']} uncommitted), "
              f"{tot['sessions']} sessions, {len(notes)} note(s).")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
