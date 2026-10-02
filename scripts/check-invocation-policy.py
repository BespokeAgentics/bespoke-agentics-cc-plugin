#!/usr/bin/env python3
"""Keep the plugin manual-only, and keep what it says about itself true.

The plugin's standing cost is its listing: every skill and command the model
may invoke puts a name and a description into every session. At v2.8.0 that was
~71k characters, added one skill at a time with nothing watching. The policy
since 2026-09-21 is that nothing triggers except manual invocation, apart from a
short allowlist of commands the plugin's own installed mandates tell an agent to
run unprompted (scripts/invocation-policy.json).

A flagged skill cannot be reached through the Skill tool -- the harness answers
"cannot be used with Skill tool due to disable-model-invocation" -- so a command,
agent or sibling skill that still dispatches that way is broken, silently, until
a user runs it. Each check below is one of those failures:

  P1  flag coverage     every skills/*/SKILL.md carries disable-model-invocation: true
  P2  command coverage  every command carries it too, except the allowlist;
                        every allowlisted name is a real command
  P3  dead dispatch     no command or agent grants Skill(<plugin skill>), and no
                        command, agent or skill tells the model to "invoke the `x`
                        skill" for a plugin skill -- it must load SKILL.md by path
  P4  loader targets    every ${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md named by a
                        command, agent or skill exists
  P5  listing budget    the descriptions that do stay in context fit the budget
  P6  agent frontmatter every agents/*.md has a name and a description and uses only
                        keys the harness reads -- `allowed-tools` belongs to skills
                        and commands; on an agent it is ignored and the agent gets
                        every tool. An empty file still registers an agent.

Exit 0 = policy holds. Exit 1 = the listing grew or a dispatch is dead.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if "--root" in sys.argv:
    REPO = Path(sys.argv[sys.argv.index("--root") + 1]).resolve()
POLICY = REPO / "scripts" / "invocation-policy.json"

FLAG = re.compile(r"^disable-model-invocation:\s*true\s*$", re.M)
# Subagent frontmatter the harness reads (code.claude.com/docs/en/sub-agents, checked 2026-10-02).
AGENT_KEYS = {
    "name", "description", "tools", "disallowedTools", "model", "permissionMode", "maxTurns",
    "skills", "mcpServers", "hooks", "memory", "background", "omitClaudeMd", "effort",
    "isolation", "color", "initialPrompt", "experimental",
}
# Eval fixtures and run outputs quote old command text on purpose.
SKIP_PARTS = {"evals", "fixtures", "node_modules"}

errors: list[str] = []


def fail(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def frontmatter(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    return (m.group(1), text[m.end():]) if m else ("", text)


def description(fm: str) -> str:
    m = re.search(r"^description:\s*(.*?)(?=^[\w-]+:|\Z)", fm, re.S | re.M)
    if not m:
        return ""
    d = m.group(1).strip()
    d = re.sub(r"^[>|][+-]?\s*\n", "", d)
    return re.sub(r"\s+", " ", d).strip().strip("\"'")


def command_name(path: Path, fm: str) -> str:
    m = re.search(r"^name:\s*[\"']?([^\"'\n]+)", fm, re.M)
    if m:
        return m.group(1).strip()
    return ":".join(path.relative_to(REPO / "commands").with_suffix("").parts)


def prose_files() -> list[Path]:
    out = []
    for base in ("commands", "agents", "skills"):
        for p in sorted((REPO / base).rglob("*.md")):
            rel = p.relative_to(REPO).parts
            if SKIP_PARTS & set(rel) or any(part.endswith("-workspace") for part in rel):
                continue
            out.append(p)
    return out


def main() -> int:
    policy = json.loads(POLICY.read_text())
    allow = set(policy["model_invocable_commands"])
    budget = int(policy["listing_budget_chars"])

    skill_files = sorted((REPO / "skills").glob("*/SKILL.md"))
    skills = {p.parent.name for p in skill_files}

    # P1
    for p in skill_files:
        fm, _ = frontmatter(p)
        if not FLAG.search(fm):
            fail(f"skills/{p.parent.name}", "P1 SKILL.md lacks disable-model-invocation: true "
                 "(a new skill is manual-only unless scripts/invocation-policy.json says otherwise)")

    # P2 + P5
    listing = 0
    seen = set()
    for p in sorted((REPO / "commands").rglob("*.md")):
        fm, _ = frontmatter(p)
        name = command_name(p, fm)
        seen.add(name)
        if name in allow:
            if FLAG.search(fm):
                fail(name, "P2 allowlisted as model-invocable but flagged manual-only")
            listing += len(name) + len(description(fm))
        elif not FLAG.search(fm):
            fail(name, "P2 command lacks disable-model-invocation: true and is not allowlisted")
    for name in sorted(allow - seen):
        fail(name, "P2 allowlisted command does not exist")
    if listing > budget:
        fail("listing", f"P5 model-visible names + descriptions total {listing} chars, budget {budget}")

    # P3 + P4
    grant = re.compile(r"Skill\(([\w-]+)\)")
    tell = re.compile(r"(?i)\binvok(?:e|es|ing) (?:the )?`([\w-]+)` skill")
    loader = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/skills/([\w-]+)/SKILL\.md")
    for p in prose_files():
        rel = p.relative_to(REPO)
        fm, body = frontmatter(p)
        for s in grant.findall(fm):
            if s in skills:
                fail(str(rel), f"P3 grants Skill({s}), which the harness refuses for a manual-only skill")
        for s in tell.findall(body):
            if s in skills:
                fail(str(rel), f"P3 tells the model to invoke the `{s}` skill; load "
                     f"${{CLAUDE_PLUGIN_ROOT}}/skills/{s}/SKILL.md by path instead")
        for s in loader.findall(body):
            if s != "<skill>" and s not in skills and not s.startswith("<"):
                fail(str(rel), f"P4 loads skills/{s}/SKILL.md, which does not exist")

    # P6
    agent_files = sorted((REPO / "agents").glob("*.md"))
    for p in agent_files:
        rel = str(p.relative_to(REPO))
        fm, _ = frontmatter(p)
        keys = re.findall(r"^([\w-]+):", fm, re.M)
        if "name" not in keys or not description(fm):
            fail(rel, "P6 agent has no name or no description (an empty file still registers an agent)")
        for k in keys:
            if k not in AGENT_KEYS:
                hint = " -- use `tools`; the harness ignores this key and grants every tool" if k == "allowed-tools" else ""
                fail(rel, f"P6 agent frontmatter key `{k}` is not one the harness reads{hint}")

    if errors:
        print("Invocation policy violated:\n")
        for e in errors:
            print(f"  FAIL  {e}")
        print(f"\n{len(errors)} problem(s).")
        return 1
    print(f"  ok  {len(skills)} skills manual-only")
    print(f"  ok  {len(seen) - len(allow)} commands manual-only, {len(allow)} model-invocable by policy")
    print(f"  ok  model-visible listing {listing} chars (budget {budget})")
    print(f"  ok  {len(agent_files)} agents declare only keys the harness reads")
    print("\nInvocation policy holds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
