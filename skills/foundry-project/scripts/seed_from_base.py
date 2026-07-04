#!/usr/bin/env python3
"""Seed a new Foundry app from the foundry-base source of truth.

Deterministic setup so every project starts identically: clone the base, drop its
git history, rename the root package, install, and verify green. The design-specific
porting happens afterwards (see plan_ports.py + the skill).

    python3 seed_from_base.py --to ../ledger-workspace --name ledger
    python3 seed_from_base.py --to ./out --name pricing --from /path/to/local/foundry-base

--from defaults to the GitHub source of truth (override with $FOUNDRY_BASE_REPO or a
local path for offline seeding).
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys

DEFAULT_BASE = os.environ.get("FOUNDRY_BASE_REPO", "https://github.com/qdhenry/foundry-base.git")


def run(cmd, cwd=None):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--to", required=True, help="target workspace directory (must be empty/new)")
    ap.add_argument("--name", required=True, help="root package name for the new app (keep @foundry/* scope)")
    ap.add_argument("--from", dest="src", default=DEFAULT_BASE, help="base repo URL or local path")
    ap.add_argument("--no-install", action="store_true", help="skip bun install + verify")
    args = ap.parse_args()

    target = pathlib.Path(args.to).resolve()
    if target.exists() and any(target.iterdir()):
        sys.exit(f"target {target} exists and is not empty")

    src = args.src
    is_local = pathlib.Path(src).expanduser().exists()
    clone = ["git", "clone"] + ([] if is_local else ["--depth", "1"]) + [str(pathlib.Path(src).expanduser()) if is_local else src, str(target)]
    run(clone)

    # fresh history — this is a new project, not a fork of the base's commits
    shutil.rmtree(target / ".git", ignore_errors=True)
    run(["git", "init", "-q"], cwd=target)

    # rename the root package (the @foundry/* package scope stays — it's the shared design system)
    pkg = target / "package.json"
    data = json.loads(pkg.read_text())
    data["name"] = args.name
    pkg.write_text(json.dumps(data, indent=2) + "\n")

    if not args.no_install:
        run(["bun", "install"], cwd=target)
        run(["bun", "run", "typecheck"], cwd=target)
        run(["bun", "run", "index:check"], cwd=target)

    print(json.dumps({
        "seeded": str(target),
        "name": args.name,
        "from": src,
        "next": "run plan_ports.py against the new design's analysis.json to get the reuse/port plan",
    }, indent=2))


if __name__ == "__main__":
    main()
