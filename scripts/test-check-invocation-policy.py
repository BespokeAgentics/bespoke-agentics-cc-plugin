#!/usr/bin/env python3
"""Prove check-invocation-policy.py still has teeth.

A policy check that passes the real tree proves nothing on its own -- zero
findings is also what a blind check reports. So this builds a small plugin that
satisfies the policy, confirms it passes, then breaks it one way at a time. Each
break is a regression that is otherwise invisible until a user runs the command:
the listing grows again, or a dispatch dies with "cannot be used with Skill tool".
"""

import json, subprocess, sys, tempfile
from pathlib import Path

CHECK = Path(__file__).resolve().parent / "check-invocation-policy.py"
ROOT = "${CLAUDE_PLUGIN_ROOT}"

GOOD = {
    "skills/alpha/SKILL.md": "---\nname: alpha\ndescription: Does alpha.\ndisable-model-invocation: true\n---\n\n# Alpha\n",
    "skills/beta/SKILL.md": (
        "---\nname: beta\ndescription: >\n  Does beta, then hands to alpha.\ndisable-model-invocation: true\n---\n\n"
        f"Load the `alpha` skill: read `{ROOT}/skills/alpha/SKILL.md` and follow it.\n"),
    "commands/open.md": (
        "---\nname: \"x:open\"\ndescription: \"Agents run this unprompted.\"\nallowed-tools: Read\n---\n\n"
        f"Read `{ROOT}/skills/alpha/SKILL.md` and follow it.\n"),
    "commands/closed.md": (
        "---\nname: \"x:closed\"\ndescription: \"Manual only.\"\nallowed-tools: Read\ndisable-model-invocation: true\n---\n\n"
        f"Read `{ROOT}/skills/beta/SKILL.md` and follow it.\n"),
    "agents/runner.md": (
        "---\nname: runner\ndescription: Runs beta.\n---\n\n"
        f"Read `{ROOT}/skills/beta/SKILL.md` and follow it.\n"),
    "scripts/invocation-policy.json": json.dumps(
        {"model_invocable_commands": ["x:open"], "listing_budget_chars": 200}),
}


def build(mutate=None) -> Path:
    files = dict(GOOD)
    if mutate:
        mutate(files)
    root = Path(tempfile.mkdtemp())
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


def run(root: Path):
    r = subprocess.run([sys.executable, str(CHECK), "--root", str(root)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def sub(rel, old, new):
    def m(files):
        assert old in files[rel], (rel, old)
        files[rel] = files[rel].replace(old, new)
    return m


def policy(**kw):
    def m(files):
        d = json.loads(files["scripts/invocation-policy.json"]); d.update(kw)
        files["scripts/invocation-policy.json"] = json.dumps(d)
    return m


cases = [
    (sub("skills/alpha/SKILL.md", "disable-model-invocation: true\n", ""),
     "P1: a new skill ships without the flag", "P1 SKILL.md lacks"),
    (sub("commands/closed.md", "disable-model-invocation: true\n", ""),
     "P2: a command ships without the flag and is not allowlisted", "P2 command lacks"),
    (policy(model_invocable_commands=["x:open", "x:renamed-away"]),
     "P2: allowlist names a command that no longer exists", "does not exist"),
    (sub("commands/open.md", "allowed-tools: Read\n", "allowed-tools: Read\ndisable-model-invocation: true\n"),
     "P2: an allowlisted command gets flagged, so agents lose it", "allowlisted as model-invocable but flagged"),
    (sub("commands/closed.md", "allowed-tools: Read\n", "allowed-tools: Skill(beta), Read\n"),
     "P3: a command dispatches a flagged skill through the Skill tool", "P3 grants Skill(beta)"),
    (sub("skills/beta/SKILL.md", "Load the `alpha` skill:", "Invoke the `alpha` skill, or"),
     "P3: a skill hands off by invoking a flagged sibling", "P3 tells the model to invoke the `alpha` skill"),
    (sub("agents/runner.md", "skills/beta/SKILL.md", "skills/gamma/SKILL.md"),
     "P4: a loader path names a skill that does not exist", "P4 loads skills/gamma/SKILL.md"),
    (sub("commands/open.md", "Agents run this unprompted.", "Agents run this unprompted. " + "Padding. " * 40),
     "P5: a model-visible description outgrows the listing budget", "P5 model-visible"),
    (sub("agents/runner.md", "description: Runs beta.\n", "description: Runs beta.\nallowed-tools: Read, Grep\n"),
     "P6: an agent limits its tools with a key the harness ignores", "P6 agent frontmatter key `allowed-tools`"),
    (lambda files: files.update({"agents/ghost.md": ""}),
     "P6: a deleted agent is left behind as an empty file", "P6 agent has no name or no description"),
]

results = []
code, out = run(build())
ok = code == 0 and "Invocation policy holds" in out
print(f"{'PASS' if ok else 'MISS'}  baseline: the untampered fixture passes")
if not ok:
    print("        exit", code, "|", out.strip().replace("\n", " | ")[:300])
results.append(ok)

for mutate, label, expect in cases:
    code, out = run(build(mutate))
    ok = code != 0 and expect in out
    print(f"{'PASS' if ok else 'MISS'}  {label}")
    if not ok:
        print("        exit", code, "|", out.strip().replace("\n", " | ")[:300])
    results.append(ok)

caught = sum(results[1:])
print(f"\n{caught}/{len(cases)} tamper cases caught" + ("" if results[0] else " -- and the baseline FAILED"))
sys.exit(0 if all(results) else 1)
