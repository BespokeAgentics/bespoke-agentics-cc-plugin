#!/usr/bin/env python3
"""Programmatic grader for project-ontology evals.

Usage: python3 grade.py <run-dir> [<run-dir> ...]

A run dir holds eval_metadata.json (eval_id), setup-hashes.json (sha256 of every file after setup),
outputs/project/ (the working copy), outputs/ANSWER.md and transcript.md. Writes grading.json next to
eval_metadata.json: {expectations: [{text, passed, evidence}], summary}.

Hooks are re-run, never trusted from a transcript: the grader executes the PreToolUse / SessionStart
commands the run installed, with the payload Claude Code would send. Checks on eval 1 are layout-agnostic
because a baseline may declare its ontology in any file format; evals 2 and 3 start from a project where
project-ontology was installed at setup, so they read its files directly.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "ontology-vault"
SEVERITIES = ["critical", "high", "medium", "low"]
TEXT_EXTS = (".yaml", ".yml", ".json", ".md", ".py", ".toml", ".txt", ".ts", ".js", ".sh")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def rel_files(root: Path, under: str = "") -> dict[str, Path]:
    base = root / under if under else root
    out = {}
    if not base.exists():
        return out
    for p in base.rglob("*"):
        if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts and "__pycache__" not in p.parts:
            out[p.relative_to(root).as_posix()] = p
    return out


def ontology_files(project: Path) -> list[Path]:
    """Files outside the content pages that declare dot-notated gap severity terms."""
    hits = []
    for rel, p in rel_files(project).items():
        if rel.startswith("wiki/clients/") or not rel.endswith(TEXT_EXTS) or rel.endswith("ANSWER.md"):
            continue
        if "gap.severity.critical" in read(p):
            hits.append(p)
    return hits


def near(text: str, needle: str, words: str, span: int = 300) -> bool:
    for m in re.finditer(re.escape(needle), text):
        window = text[max(0, m.start() - span): m.end() + span]
        if re.search(words, window, re.I):
            return True
    return False


def frontmatter(text: str) -> dict:
    m = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            km = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
            if km:
                out[km.group(1)] = km.group(2).strip().strip('"').strip("'")
    return out


def settings(project: Path) -> dict:
    try:
        return json.loads(read(project / ".claude" / "settings.json") or "{}")
    except ValueError:
        return {}


def hook_commands(project: Path, event: str, tool: str | None) -> list[str]:
    cmds = []
    for entry in settings(project).get("hooks", {}).get(event, []) or []:
        matcher = entry.get("matcher")
        if tool and matcher:
            try:
                if not re.fullmatch(matcher, tool) and not re.search(rf"(^|\|){re.escape(tool)}(\||$)", matcher):
                    continue
            except re.error:
                if tool not in matcher:
                    continue
        for h in entry.get("hooks", []):
            if h.get("type", "command") == "command" and h.get("command"):
                cmds.append(h["command"])
    return cmds


def run_pre(project: Path, tool: str, tool_input: dict) -> tuple[bool, str, list[int]]:
    """Run every PreToolUse command matching the tool. Blocked when any exits 2 or returns a deny decision."""
    payload = {"session_id": "grader", "hook_event_name": "PreToolUse", "cwd": str(project), "tool_name": tool,
               "tool_input": tool_input}
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project))
    blocked, out, codes = False, "", []
    for cmd in hook_commands(project, "PreToolUse", tool):
        try:
            p = subprocess.run(["bash", "-c", cmd], input=json.dumps(payload), capture_output=True, text=True, cwd=project, env=env, timeout=60)
        except subprocess.TimeoutExpired:
            codes.append(-1)
            continue
        codes.append(p.returncode)
        out += p.stdout + p.stderr
        if p.returncode == 2:
            blocked = True
        try:
            d = json.loads(p.stdout or "{}")
            hso = d.get("hookSpecificOutput") or {}
            if hso.get("permissionDecision") == "deny" or d.get("decision") in ("block", "deny"):
                blocked = True
        except ValueError:
            pass
    return blocked, out, codes


def content_changes(project: Path, run_dir: Path, allow_new: set[str] | None = None) -> list[str]:
    setup = json.loads(read(run_dir / "setup-hashes.json") or "{}")
    now = {rel: sha(p) for rel, p in rel_files(project, "wiki/clients").items()}
    changed = []
    for rel, h in setup.items():
        if rel.startswith("wiki/clients/") and now.get(rel) != h:
            changed.append(rel)
    for rel in now:
        if rel not in setup and not (allow_new and any(re.fullmatch(a, rel) for a in allow_new)):
            changed.append(rel + " (new)")
    return changed


def crosslink_only_changes(project: Path, run_dir: Path, new_rels: list[str]) -> list[str]:
    """Pre-existing content pages whose change is more than adding cross-links to the new page(s): the
    Wiki-First Mandate asks for bidirectional links, so a backlink (plus an `updated:` bump) is expected;
    anything else — a value rewritten, text removed — is reported."""
    import difflib
    setup = json.loads(read(run_dir / "setup-hashes.json") or "{}")
    stems = [Path(r).stem for r in new_rels]
    link = re.compile(r"\[\[(?:[^\]|]*/)?(" + "|".join(map(re.escape, stems)) + r")(?:\|[^\]]*)?\]\]") if stems else None
    bad = []
    for rel, h in setup.items():
        if not rel.startswith("wiki/clients/"):
            continue
        p = project / rel
        if not p.exists():
            bad.append(rel + " (deleted)")
            continue
        if sha(p) == h:
            continue
        old, new = read(FIXTURE / rel), read(p)
        fo, fn = frontmatter(old), frontmatter(new)
        fo.pop("updated", None)
        fn.pop("updated", None)
        if fo != fn:
            bad.append(rel + " (frontmatter values changed)")
            continue
        ob = old.split("\n---", 2)[-1].splitlines()
        nb = new.split("\n---", 2)[-1].splitlines()
        ok = True
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ob, nb).get_opcodes():
            added = "\n".join(nb[j1:j2])
            if tag == "equal":
                continue
            if tag == "delete" or not (link and link.search(added)):
                ok = False
            elif tag == "replace" and not all(line.strip() in added for line in ob[i1:i2]):
                ok = False
        if not ok:
            bad.append(rel + " (body changed beyond a cross-link)")
    return bad


def new_content(project: Path, run_dir: Path, rel: str) -> str:
    """Text added to a file since setup: compared with the copy setup saved (setup-<name>), else the fixture."""
    text = read(project / rel)
    saved = run_dir / f"setup-{Path(rel).name}"
    base = saved if saved.exists() else FIXTURE / rel
    if base.exists():
        b = read(base)
        return text[len(b.rstrip(chr(10))):] if text.startswith(b.rstrip("\n")) else text
    return text


def grade_eval1(run_dir: Path, project: Path, answer: str) -> list[tuple[str, bool, str]]:
    exp = []
    onto = ontology_files(project)
    exp.append((f"dot-notated ontology with gap.severity.critical", bool(onto), f"files: {[p.relative_to(project).as_posix() for p in onto][:4]}"))
    sev_ok = any(all(f"gap.severity.{s}" in read(p) for s in SEVERITIES) for p in onto)
    exp.append(("all four severities allowed", sev_ok, "gap.severity.{critical,high,medium,low} in one declaration" if sev_ok else "not all four found in one file"))
    # "flagged" is judged by meaning, not by one vocabulary: a baseline wrote "Accept P0, or re-rate the page"
    # in a review list, which is flagging for review in plain words
    flag_words = r"proposed|pending|review|unapproved|candidate|flag|decide|accept|re-rate|undeclared|not declared|awaiting"
    p0_ok, p0_ev = False, "P0 not found as flagged"
    for p in onto:
        lines = read(p).splitlines()
        for i, ln in enumerate(lines):
            if re.search(r"\bp0\b", ln, re.I):
                block = "\n".join(lines[max(0, i - 3):i + 8])
                if re.search(flag_words, block, re.I) and not re.search(r"status\W+approved\b", "\n".join(lines[i:i + 8]), re.I):
                    p0_ok, p0_ev = True, f"{p.name}: {ln.strip()[:120]} … flagged in its block"
                    break
        if p0_ok:
            break
    if not p0_ok and near(answer, "P0", flag_words, 300) and not near(answer, "P0", r"\bapproved\b(?!.*pending)", 40):
        p0_ok, p0_ev = True, "ANSWER.md flags P0 for review"
    exp.append(("P0 not silently approved", p0_ok, p0_ev))
    blob = answer + "\n".join(read(p) for p in onto)
    nt = near(blob, "Northwind Traders", r"alias|variant|noncanonical|spelling|misspell|inconsistent|canonical", 300)
    exp.append(("Northwind Traders identified as a variant of northwind", nt, "found near alias/variant wording" if nt else "not identified"))
    pre_cmds = hook_commands(project, "PreToolUse", "Write") + hook_commands(project, "PreToolUse", "Edit")
    exp.append(("PreToolUse Write/Edit hook registered", bool(pre_cmds), f"{len(pre_cmds)} command(s)"))
    new_rel = "wiki/clients/northwind/gaps/payment-terms.md"
    body = "---\ntype: gap\nclient: northwind\nstatus: open\nseverity: {sev}\ncreated: 2026-09-17\nupdated: 2026-09-17\n---\n\n# Payment Terms\n\nNet-30 terms are not enforced at checkout.\n"
    target = str(project / new_rel)
    blocked, out, codes = run_pre(project, "Write", {"file_path": target, "path": target, "content": body.format(sev="urgent"), "contents": body.format(sev="urgent")})
    named = sum(1 for s in SEVERITIES if re.search(rf"\b{s}\b", out))
    exp.append(("hook blocks severity urgent naming approved severities", blocked and named >= 3, f"blocked={blocked} exit={codes} severities named={named}"))
    blocked2, out2, codes2 = run_pre(project, "Write", {"file_path": target, "path": target, "content": body.format(sev="high"), "contents": body.format(sev="high")})
    exp.append(("hook allows a valid gap (severity high)", bool(pre_cmds) and not blocked2, f"blocked={blocked2} exit={codes2} {out2.strip()[:160]}"))
    edit_target = str(project / "wiki/clients/northwind/gaps/credit-limit-enforcement.md")
    blocked3, out3, codes3 = run_pre(project, "Edit", {"file_path": edit_target, "path": edit_target, "old_string": "# Credit Limit Enforcement", "new_string": "# Credit Limit Enforcement at Checkout", "replace_all": False})
    exp.append(("ratchet: unrelated edit on a page with a pre-existing violation is allowed", bool(pre_cmds) and not blocked3, f"blocked={blocked3} exit={codes3} {out3.strip()[:160]}"))
    cm = read(project / "CLAUDE.md")
    cm_ok = bool(re.search(r"ontolog", cm, re.I) and re.search(r"propos|register|add(ing)? (a )?(new )?term", cm, re.I) and re.search(r"approv", cm, re.I))
    exp.append(("CLAUDE.md: use ontology values; how terms are added and approved", cm_ok, f"CLAUDE.md {len(cm)} chars"))
    ss = hook_commands(project, "SessionStart", None)
    ss_ok = False
    for c in ss:
        script = re.sub(r"\$\{?CLAUDE_PROJECT_DIR\}?", str(project), c).split()[0]
        if "ontolog" in c.lower() or "ontolog" in read(Path(script)).lower():
            ss_ok = True
    exp.append(("SessionStart hook surfaces the ontology", ss_ok, f"{len(ss)} SessionStart command(s)"))
    changes = content_changes(project, run_dir)
    exp.append(("no content page rewritten", not changes, f"changed: {changes[:5]}" if changes else "wiki/clients unchanged"))
    return exp


def load_engine(project: Path):
    import importlib.util
    path = project / ".claude" / "ontology" / "ontology.py"
    spec = importlib.util.spec_from_file_location(f"onto_{abs(hash(str(project)))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def grade_eval2(run_dir: Path, project: Path, answer: str) -> list[tuple[str, bool, str]]:
    exp = []
    setup = json.loads(read(run_dir / "setup-hashes.json") or "{}")
    new_pages = [p for rel, p in rel_files(project, "wiki/clients/northwind/gaps").items() if rel not in setup]
    page = next((p for p in new_pages if frontmatter(read(p)).get("severity") == "urgent"), None)
    exp.append(("new gap page with severity urgent", page is not None, page.relative_to(project).as_posix() if page else f"new pages: {[p.name for p in new_pages]}"))
    fm = frontmatter(read(page)) if page else {}
    exp.append(("canonical client northwind", fm.get("client") == "northwind", f"client: {fm.get('client')}"))
    term, onto_err = None, ""
    try:
        eng = load_engine(project)
        onto = eng.Ontology(eng.parse_onto_yaml(read(project / "wiki/_schema/ontology.yaml")))
        term = onto.terms.get("gap.severity.urgent")
    except Exception as e:
        onto_err = str(e)
    exp.append(("gap.severity.urgent approved", bool(term and term.get("status") == "approved"), f"status: {term.get('status') if term else None} {onto_err}"))
    exp.append(("approval attributed to Jordan Lee", bool(term and "jordan" in str(term.get("approved-by", "")).lower()), f"approved-by: {term.get('approved-by') if term else None}"))
    exp.append(("term has a definition", bool(term and str(term.get("definition") or "").strip()), f"definition: {(term or {}).get('definition')}"))
    rf = fm.get("related-feature", "")
    exp.append(("related-feature links canonically to credit-limits", bool(re.search(r"\[\[credit-limits(\|[^\]]*)?\]\]", rf)), f"related-feature: {rf}"))
    viol_ok, viol_ev = False, "no page"
    if page:
        p = subprocess.run(["python3", ".claude/ontology/ontology.py", "check", page.relative_to(project).as_posix(), "--format", "json"], cwd=project, capture_output=True, text=True)
        try:
            vs = json.loads(p.stdout)["violations"]
            bad = [v for v in vs if v.get("policy") == "strict" or v.get("field") == "severity"]
            viol_ok, viol_ev = not bad, f"{len(vs)} violation(s); blocking/severity: {[(v['rule'], v.get('value')) for v in bad]}"
        except (ValueError, KeyError) as e:
            viol_ev = f"check failed: {e} {p.stderr[:200]}"
    exp.append(("no strict or severity violation on the new page (engine)", viol_ok, viol_ev))
    log_new = new_content(project, run_dir, "wiki/_log.md")
    exp.append(("governance change logged", "urgent" in log_new.lower(), f"{len(log_new)} new chars in _log.md"))
    exp.append(("ONTOLOGY.md lists gap.severity.urgent", "gap.severity.urgent" in read(project / "wiki/_schema/ONTOLOGY.md"), "checked ONTOLOGY.md"))
    new_rels = [p.relative_to(project).as_posix() for p in new_pages]
    bad = crosslink_only_changes(project, run_dir, new_rels)
    exp.append(("pre-existing content pages changed only to cross-link the new page", not bad, f"beyond cross-links: {bad[:5]}" if bad else "unchanged or backlinks only"))
    return exp


def grade_eval3(run_dir: Path, project: Path, answer: str) -> list[tuple[str, bool, str]]:
    exp = []
    setup = json.loads(read(run_dir / "setup-hashes.json") or "{}")
    reports = [p for rel, p in rel_files(project, "wiki").items() if rel not in setup and "lint" in rel.lower() and rel.endswith(".md")]
    rep = "\n".join(read(p) for p in reports)
    exp.append(("lint report exists under wiki/", bool(reports), f"{[p.relative_to(project).as_posix() for p in reports]}"))
    exp.append(("report has an ontology dimension", bool(re.search(r"ontolog", rep, re.I)), "ontology wording present" if re.search(r"ontolog", rep, re.I) else "absent"))
    exp.append(("relation-range in bulk-import reported", near(rep, "bulk-import", r"relation-range|range|expects feature|points at a .?gap|not a feature", 400), "bulk-import near range wording"))
    exp.append(("Northwind Traders reported as noncanonical", near(rep, "Northwind Traders", r"noncanonical|variant|alias|canonical|spelling", 400), "variant wording near Northwind Traders"))
    exp.append(("broken [[missing-vendor-eval]] reported", "missing-vendor-eval" in rep, "present" if "missing-vendor-eval" in rep else "absent"))
    exp.append(("P0 reported as proposed awaiting approval", near(rep, "P0", r"propos|approv|pending", 300), "P0 near proposal wording"))
    changed = []
    for rel, h in setup.items():
        if rel.startswith("wiki/clients/") or rel.startswith("wiki/_schema/"):
            p = project / rel
            if not p.exists() or sha(p) != h:
                changed.append(rel)
    exp.append(("no content page or ontology file modified", not changed, f"changed: {changed[:5]}" if changed else "unchanged"))
    log_new = new_content(project, run_dir, "wiki/_log.md")
    exp.append(("lint run logged in _log.md", bool(re.search(r"lint", log_new, re.I)), f"{len(log_new)} new chars"))
    return exp


def grade(run_dir: Path) -> dict:
    meta = json.loads(read(run_dir / "eval_metadata.json"))
    project = run_dir / "outputs" / "project"
    answer = read(run_dir / "outputs" / "ANSWER.md") + read(project / "ANSWER.md")
    fn = {1: grade_eval1, 2: grade_eval2, 3: grade_eval3}[meta["eval_id"]]
    exp = fn(run_dir, project, answer)
    texts = meta.get("assertions") or [e[0] for e in exp]
    results = [{"text": texts[i] if i < len(texts) else e[0], "passed": bool(e[1]), "evidence": e[2]} for i, e in enumerate(exp)]
    passed = sum(r["passed"] for r in results)
    out = {"expectations": results, "summary": {"passed": passed, "failed": len(results) - passed, "total": len(results),
                                                "pass_rate": round(passed / len(results), 4) if results else 0}}
    (run_dir / "grading.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    for d in sys.argv[1:]:
        r = grade(Path(d))
        print(f"{d}: {r['summary']['passed']}/{r['summary']['total']}")
        for e in r["expectations"]:
            print(f"  {'PASS' if e['passed'] else 'FAIL'}  {e['text']} — {e['evidence']}")
