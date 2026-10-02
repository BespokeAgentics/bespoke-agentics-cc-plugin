#!/usr/bin/env python3
"""Keep plugin hook timeouts in seconds.

Claude Code and Codex both read a command hook's `timeout` in seconds. A value written in
milliseconds (`"timeout": 10000`) still parses, still installs, and lets a hung
hook block the session for hours. Nothing else notices: the plugin's own hook
and two skills that teach users to write hooks carried millisecond values until
the 2026-09-28 prompt audit.

Scans the plugin's Claude Code hook file (`hooks/hooks.json`), its Codex hook
file (root `hooks.json`, named by `.codex-plugin/plugin.json`), and every skill file that shows or
installs a hook config, and fails on any literal `"timeout": N` above the
ceiling. Placeholders (`{{TIMEOUT_SECONDS}}`) are not numbers and are skipped.

Not scanned: `.claude/`, which is local configuration.

  python3 scripts/check-hook-timeouts.py            # check the repo
  python3 scripts/check-hook-timeouts.py --self-test

Exit 0 = every timeout is plausible seconds. Exit 1 = at least one is not.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CEILING_SECONDS = 600  # ten minutes; anything above it is almost certainly milliseconds
TIMEOUT = re.compile(r'"timeout"\s*:\s*(\d+)')
SUFFIXES = {".json", ".md", ".template", ".tmpl"}
SKIP_PARTS = {"evals", "node_modules"}


def targets(root: Path) -> list[Path]:
    files = [root / "hooks" / "hooks.json", root / "hooks.json"]
    for p in sorted((root / "skills").rglob("*")):
        if p.suffix not in SUFFIXES or not p.is_file():
            continue
        rel = p.relative_to(root).parts
        if SKIP_PARTS.intersection(rel) or rel[1].endswith("-workspace"):
            continue
        files.append(p)
    return [f for f in files if f.is_file()]


def violations(root: Path) -> list[str]:
    found = []
    for path in targets(root):
        for n, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            for value in TIMEOUT.findall(line):
                if int(value) > CEILING_SECONDS:
                    found.append(f"{path.relative_to(root)}:{n}: \"timeout\": {value} "
                                 f"(seconds; > {CEILING_SECONDS} — written in milliseconds?)")
    return found


def self_test() -> int:
    cases = {
        "plugin hook in ms": ("hooks/hooks.json", '{"hooks": [{"timeout": 10000}]}', 1),
        "codex hook in ms": ("hooks.json", '{"hooks": [{"timeout": 10000}]}', 1),
        "skill example in ms": ("skills/x/SKILL.md", '    "timeout": 5000\n', 1),
        "seconds pass": ("skills/x/SKILL.md", '"timeout": 30\n', 0),
        "placeholder skipped": ("skills/x/t.template", '"timeout": {{TIMEOUT_SECONDS}}\n', 0),
        "eval output ignored": ("skills/x/evals/out.json", '"timeout": 90000\n', 0),
    }
    failed = 0
    for name, (rel, body, expected) in cases.items():
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills").mkdir()
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(body)
            got = len(violations(root))
            ok = got == expected
            failed += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {name} (expected {expected}, got {got})")
    print(f"\n{len(cases) - failed}/{len(cases)} cases behave")
    return 1 if failed else 0


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        return self_test()
    found = violations(ROOT)
    for v in found:
        print(f"FAIL  {v}")
    if found:
        return 1
    print(f"ok  {len(targets(ROOT))} files, every hook timeout ≤ {CEILING_SECONDS}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
