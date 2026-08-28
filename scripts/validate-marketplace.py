#!/usr/bin/env python3
"""Validate .claude-plugin/marketplace.json before it reaches an install.

Every check here exists because the corresponding failure was found by a user
clicking Install, not by anything in this repo:

  C1  source type      "github:owner/repo" is not a source, and "git" is a
                       MARKETPLACE source type that plugin entries reject.
                       Plugin sources: github, git-subdir, npm, url, archive,
                       command.
  C2  reachability     the "github" type clones over git@github.com, which
                       needs an SSH key. Checked with credentials forced OFF,
                       so a machine that happens to have a key cannot report
                       green on behalf of one that does not.
  C3  pin freshness    a url source pins a sha. Pushing the fork does not move
                       it, so the pin goes stale silently.
  C4  loadability      the pinned tree must actually carry a plugin manifest
                       whose declared skills path exists.
  C5  version parity   marketplace.json and plugin.json drifted once already
                       (2.1.0 vs 2.2.0) and nothing noticed.

Exit 0 = safe to push. Exit 1 = an install would fail or serve a stale tree.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"

if "--file" in sys.argv:
    MARKETPLACE = Path(sys.argv[sys.argv.index("--file") + 1]).resolve()

# Accepted by a PLUGIN entry. "git" is deliberately absent: it is valid for a
# marketplace source and rejected for a plugin source, which is exactly the
# trap that cost an install attempt.
PLUGIN_SOURCE_TYPES = {"github", "git-subdir", "npm", "url", "archive", "command"}
GIT_REMOTE_TYPES = {"github", "git-subdir", "url"}

errors: list[str] = []
notes: list[str] = []


def fail(entry: str, msg: str) -> None:
    errors.append(f"{entry}: {msg}")


def note(msg: str) -> None:
    notes.append(msg)


def bare_git_env() -> dict[str, str]:
    """git with every credential path shut off.

    Without this the check passes on a machine holding an SSH key or a
    credential helper and fails for everyone else -- which is the shape of the
    bug it is meant to catch. GIT_CONFIG_GLOBAL=/dev/null also neutralises any
    url.insteadOf rewrite that would quietly turn ssh into https.
    """
    env = dict(os.environ)
    env.pop("SSH_AUTH_SOCK", None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "/bin/echo"
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"
    env["GIT_SSH_COMMAND"] = (
        "ssh -o BatchMode=yes -o IdentitiesOnly=yes "
        "-o IdentityFile=/dev/null -o StrictHostKeyChecking=no"
    )
    return env


def git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        env=bare_git_env(),
        capture_output=True,
        text=True,
        timeout=120,
    )


def check_local(name: str, rel: str, declared_version: str | None) -> None:
    root = (REPO / rel).resolve()
    manifest = root / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        fail(name, f'relative source "{rel}" has no .claude-plugin/plugin.json')
        return
    note(f'{name}: local source "{rel}" at v{declared_version}')
    check_manifest(name, manifest, declared_version, root)


def check_manifest(
    name: str, manifest: Path, declared_version: str | None, root: Path
) -> None:
    try:
        plugin = json.loads(manifest.read_text())
    except json.JSONDecodeError as exc:
        fail(name, f"plugin.json is not valid JSON: {exc}")
        return

    if plugin.get("name") != name:
        fail(name, f'plugin.json declares name "{plugin.get("name")}"')

    # C5
    if declared_version and plugin.get("version") != declared_version:
        fail(
            name,
            f'version drift: marketplace says {declared_version}, '
            f'plugin.json says {plugin.get("version")}',
        )

    # C4
    skills_rel = plugin.get("skills")
    if skills_rel:
        skills_dir = (root / skills_rel).resolve()
        if not skills_dir.is_dir():
            fail(name, f'declared skills path "{skills_rel}" does not exist')
        else:
            found = sorted(p.name for p in skills_dir.iterdir() if (p / "SKILL.md").is_file())
            if not found:
                fail(name, f'skills path "{skills_rel}" holds no skill with a SKILL.md')
            else:
                note(f"{name}: {len(found)} skill(s) -> {', '.join(found[:6])}")


def check_remote(name: str, src: dict, declared_version: str | None) -> None:
    kind = src.get("source")

    # C1
    if kind not in PLUGIN_SOURCE_TYPES:
        extra = ""
        if kind == "git":
            extra = ' -- "git" is a marketplace source type; plugin entries reject it. Use "url".'
        fail(
            name,
            f'source type "{kind}" is not one of {sorted(PLUGIN_SOURCE_TYPES)}{extra}',
        )
        return

    if kind == "github":
        fail(
            name,
            'the "github" source clones over git@github.com and fails without an '
            'SSH key on the machine. Use {"source": "url", "url": "https://...git", "sha": "..."}.',
        )
        return

    if kind not in GIT_REMOTE_TYPES:
        note(f"{name}: source type {kind} is not git-backed; not checked further")
        return

    url = src.get("url")
    if not url:
        fail(name, f'source type "{kind}" needs a url')
        return
    if url.startswith("git@") or url.startswith("ssh://"):
        fail(name, f"url {url} is an SSH endpoint and needs a key on every install machine")
        return

    # C2 -- reachable with no credentials at all
    ls = git(["ls-remote", url, "HEAD", "refs/heads/main", "refs/heads/master"])
    if ls.returncode != 0:
        fail(name, f"not reachable anonymously over https: {ls.stderr.strip().splitlines()[-1:] or ls.stderr.strip()}")
        return

    refs = {}
    for line in ls.stdout.strip().splitlines():
        sha, ref = line.split("\t")
        refs[ref] = sha
    head = refs.get("refs/heads/main") or refs.get("refs/heads/master") or refs.get("HEAD")

    sha = src.get("sha")
    if not sha:
        fail(
            name,
            "no pinned sha. Every remote entry in the official marketplace pins one; "
            f"without it the installed tree is whatever the branch happens to be. Add: "
            f'"sha": "{head}"',
        )
        return

    # C3
    if head and sha != head:
        fail(
            name,
            f"pinned sha is stale.\n"
            f"    pinned:  {sha}\n"
            f"    remote:  {head}\n"
            f'    bump it:  python3 scripts/validate-marketplace.py --bump {name}',
        )
        return

    # C4 -- the pinned tree must actually load
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for cmd in (["init", "-q"], ["remote", "add", "origin", url]):
            r = git(cmd, cwd=work)
            if r.returncode != 0:
                fail(name, f"git {cmd[0]} failed: {r.stderr.strip()}")
                return
        r = git(["fetch", "-q", "--depth", "1", "origin", sha], cwd=work)
        if r.returncode != 0:
            fail(name, f"cannot fetch pinned sha {sha[:8]}: {r.stderr.strip()}")
            return
        r = git(["checkout", "-q", "FETCH_HEAD"], cwd=work)
        if r.returncode != 0:
            fail(name, f"cannot check out pinned sha: {r.stderr.strip()}")
            return

        sub = src.get("path")
        root = (work / sub) if sub else work
        manifest = root / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            fail(name, f"pinned tree has no .claude-plugin/plugin.json")
            return
        check_manifest(name, manifest, declared_version, root)


def bump(target: str) -> int:
    data = json.loads(MARKETPLACE.read_text())
    changed = False
    for entry in data.get("plugins", []):
        if entry.get("name") != target:
            continue
        src = entry.get("source")
        if not isinstance(src, dict) or "url" not in src:
            print(f"{target}: not a pinned remote source", file=sys.stderr)
            return 1
        ls = git(["ls-remote", src["url"], "refs/heads/main", "refs/heads/master"])
        if ls.returncode != 0:
            print(f"{target}: ls-remote failed\n{ls.stderr}", file=sys.stderr)
            return 1
        head = ls.stdout.split("\t")[0].strip()
        if src.get("sha") == head:
            print(f"{target}: already at {head}")
            return 0
        print(f"{target}: {src.get('sha')} -> {head}")
        src["sha"] = head
        changed = True
    if not changed:
        print(f"{target}: not found in marketplace.json", file=sys.stderr)
        return 1
    MARKETPLACE.write_text(json.dumps(data, indent=2) + "\n")
    return 0


def main() -> int:
    if "--bump" in sys.argv:
        return bump(sys.argv[sys.argv.index("--bump") + 1])

    if not MARKETPLACE.is_file():
        print(f"no marketplace at {MARKETPLACE}", file=sys.stderr)
        return 1
    data = json.loads(MARKETPLACE.read_text())

    for entry in data.get("plugins", []):
        name = entry.get("name", "<unnamed>")
        src = entry.get("source")
        version = entry.get("version")
        if isinstance(src, str):
            if not src.startswith("./"):
                fail(
                    name,
                    f'bare string source "{src}" means a relative path only. '
                    "A remote needs an object.",
                )
                continue
            check_local(name, src, version)
        elif isinstance(src, dict):
            check_remote(name, src, version)
        else:
            fail(name, f"source must be a relative path string or an object, got {type(src).__name__}")

    for n in notes:
        print(f"  ok  {n}")
    if errors:
        print()
        for e in errors:
            print(f"FAIL  {e}")
        print(f"\n{len(errors)} problem(s). An install would fail or serve a stale tree.")
        return 1
    print(f"\nAll {len(data.get('plugins', []))} entries install-clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
