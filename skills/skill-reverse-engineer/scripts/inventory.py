#!/usr/bin/env python3
"""Deterministic inventory of a Claude Code skill directory.

Usage: inventory.py <skill-dir> [--json]

Emits metrics that seed the skill-reverse-engineer report: file tree by role,
SKILL.md size and prose/code split, ALL-CAPS directive counts, vague-quantifier
counts, verify-verb lines, internal-reference integrity, and per-script hygiene.

Exit codes: 0 ok · 1 usage error · 2 target is not a skill directory.
"""

import json
import os
import re
import stat
import sys

ROLE_DIRS = ("scripts", "references", "templates", "assets", "agents", "evals")

CAPS_DIRECTIVES = ("MUST", "NEVER", "ALWAYS")

VAGUE_QUANTIFIERS = (
    "as needed",
    "if appropriate",
    "when appropriate",
    "where appropriate",
    "when relevant",
    "if relevant",
    "as necessary",
    "where necessary",
    "if needed",
    "if applicable",
    "when applicable",
)

VERIFY_VERBS = re.compile(
    r"\b(verify|ensure|confirm|make sure|check that|double-check)\b", re.IGNORECASE
)

# Relative paths into bundled dirs, e.g. references/rules.md, scripts/foo.sh.
# The final segment must carry an extension so slash-joined prose lists of the
# role dirs don't false-positive. Matches are candidates: illustrative example
# paths inside a skill's docs will surface as "broken" — verify before filing.
REF_PATH = re.compile(
    r"(?<![\w/.-])((?:%s)/(?:[\w.-]+/)*[\w-]+\.[\w]+)" % "|".join(ROLE_DIRS)
)

ARG_HANDLING = re.compile(
    r"argparse|getopts|sys\.argv|click|typer|\$\{?1|\"\$1\"|process\.argv|ARGV"
)


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def split_prose_code(text):
    """Return (prose_lines, code_lines, fence_blocks) for a markdown text."""
    prose = code = blocks = 0
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if not in_fence:
                blocks += 1
            in_fence = not in_fence
            continue
        if in_fence:
            code += 1
        elif line.strip():
            prose += 1
    return prose, code, blocks


def count_occurrences(text, needles, case_sensitive):
    hay = text if case_sensitive else text.lower()
    return {
        n: hay.count(n if case_sensitive else n.lower())
        for n in needles
        if hay.count(n if case_sensitive else n.lower())
    }


def markdown_files(skill_dir):
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
        for name in files:
            if name.endswith(".md"):
                yield os.path.join(root, name)


def script_hygiene(path):
    text = read_text(path) or ""
    mode = os.stat(path).st_mode
    return {
        "path": path,
        "lines": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
        "shebang": text.startswith("#!"),
        "executable": bool(mode & stat.S_IXUSR),
        "arg_handling": bool(ARG_HANDLING.search(text)),
        "silent_failure_constructs": len(
            re.findall(r"\|\|\s*true|except\s*:\s*pass", text)
        ),
    }


def main(argv):
    args = [a for a in argv[1:] if a != "--json"]
    as_json = "--json" in argv[1:]
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stderr)
        return 1

    skill_dir = os.path.abspath(args[0])
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isdir(skill_dir) or not os.path.isfile(skill_md):
        print(f"error: {skill_dir} is not a skill directory (no SKILL.md)", file=sys.stderr)
        return 2

    text = read_text(skill_md)
    prose, code, blocks = split_prose_code(text)

    result = {
        "skill_dir": skill_dir,
        "skill_md": {
            "lines": text.count("\n") + 1,
            "words": len(text.split()),
            "prose_lines": prose,
            "fenced_code_lines": code,
            "fenced_blocks": blocks,
        },
        "bundles": {},
        "caps_directives": {},
        "vague_quantifiers": {},
        "verify_verb_lines": 0,
        "internal_references": {"resolved": [], "broken": []},
        "scripts": [],
    }

    for role in ROLE_DIRS:
        d = os.path.join(skill_dir, role)
        if os.path.isdir(d):
            names = sorted(
                os.path.join(dp, f)[len(skill_dir) + 1 :]
                for dp, _, fs in os.walk(d)
                for f in fs
            )
            result["bundles"][role] = names

    seen_refs = set()
    for md in markdown_files(skill_dir):
        md_text = read_text(md) or ""
        rel = os.path.relpath(md, skill_dir)
        for k, v in count_occurrences(md_text, CAPS_DIRECTIVES, True).items():
            result["caps_directives"][k] = result["caps_directives"].get(k, 0) + v
        for k, v in count_occurrences(md_text, VAGUE_QUANTIFIERS, False).items():
            result["vague_quantifiers"][k] = result["vague_quantifiers"].get(k, 0) + v
        result["verify_verb_lines"] += sum(
            1 for line in md_text.splitlines() if VERIFY_VERBS.search(line)
        )
        for m in REF_PATH.finditer(md_text):
            ref = m.group(1).rstrip(".,)")
            key = (rel, ref)
            if key in seen_refs:
                continue
            seen_refs.add(key)
            bucket = (
                "resolved"
                if os.path.exists(os.path.join(skill_dir, ref))
                else "broken"
            )
            result["internal_references"][bucket].append({"in": rel, "ref": ref})

    for rel in result["bundles"].get("scripts", []):
        result["scripts"].append(
            {**script_hygiene(os.path.join(skill_dir, rel)), "path": rel}
        )

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        s = result["skill_md"]
        print(f"skill: {skill_dir}")
        print(
            f"SKILL.md: {s['lines']} lines, {s['words']} words "
            f"({s['prose_lines']} prose / {s['fenced_code_lines']} fenced-code lines, "
            f"{s['fenced_blocks']} blocks)"
        )
        for role in ROLE_DIRS:
            if role in result["bundles"]:
                print(f"{role}/: {len(result['bundles'][role])} file(s)")
        print(f"ALL-CAPS directives: {result['caps_directives'] or 0}")
        print(f"vague quantifiers: {result['vague_quantifiers'] or 0}")
        print(f"verify-verb lines: {result['verify_verb_lines']}")
        broken = result["internal_references"]["broken"]
        print(
            f"internal refs: {len(result['internal_references']['resolved'])} resolved, "
            f"{len(broken)} broken"
        )
        for b in broken:
            print(f"  BROKEN: {b['ref']} (in {b['in']})")
        for sc in result["scripts"]:
            flags = [
                k
                for k, ok in (
                    ("no-shebang", not sc["shebang"]),
                    ("not-executable", not sc["executable"]),
                    ("no-arg-handling", not sc["arg_handling"]),
                )
                if ok
            ]
            if sc["silent_failure_constructs"]:
                flags.append(f"silent-failure×{sc['silent_failure_constructs']}")
            print(f"script {sc['path']}: {', '.join(flags) or 'ok'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
