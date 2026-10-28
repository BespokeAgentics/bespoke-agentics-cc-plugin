#!/usr/bin/env python3
"""Check, fill, render and tally an edge-case matrix (cases.json).

Stdlib only. Deterministic.

    python3 check_cases.py cases.json                  # validate; exit 1 on any error
    python3 check_cases.py cases.json --fill           # compute priorities, sort, trim (quick); write back
    python3 check_cases.py cases.json --final          # also require verification at deep/prove
    python3 check_cases.py cases.json --markdown OUT   # render the case matrix table to OUT
    python3 check_cases.py cases.json --summary        # print tallies as JSON
    python3 check_cases.py cases.json --repo DIR       # also check every cited code file:line exists

The contract is assets/templates/case.schema.json plus the cross-field rules below, documented in
references/analysts.md. Keep the three in step.

Exit codes: 0 valid (warnings allowed), 1 contract errors, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

LENSES = ["input", "state", "timing", "failure", "actors", "security", "scale",
          "environment", "ux", "domain", "change", "interaction"]
KINDS = {"plan", "feature", "changes"}
LEVELS = ["quick", "standard", "deep", "prove"]
SOURCES = {"spec", "convention", "proposed"}
DECISIONS = {"uncontested", "needed", "decided", "open"}
STATUSES = ["HANDLED", "PARTIAL", "UNHANDLED", "UNKNOWN", "N/A"]
VERIFICATIONS = {"as-read", "upheld", "overturned", "probe-confirmed", "probe-not-reproduced",
                 "probe-inconclusive", "n/a"}
SEVERITIES = ["critical", "high", "medium", "low"]
LIKELIHOODS = ["likely", "possible", "rare"]
PRIORITIES = ["P0", "P1", "P2", "P3"]
ORIGINS = {"introduced", "pre-existing"}
MATRIX = {
    "critical": {"likely": "P0", "possible": "P0", "rare": "P1"},
    "high": {"likely": "P0", "possible": "P1", "rare": "P2"},
    "medium": {"likely": "P1", "possible": "P2", "rare": "P3"},
    "low": {"likely": "P2", "possible": "P3", "rare": "P3"},
}
REQUIRED = ["id", "lens", "title", "given", "when", "then", "expected_source", "expected_evidence",
            "current_status", "verification", "severity", "likelihood", "stems_from", "test_idea"]
QUICK_CAP = 12
CASE_ID = re.compile(r"^EC-\d{2,}$")
# path:line — the path must contain a "/" or "." (so "10:30" is not a location), or be a
# well-known extensionless file name.
LOCATION = re.compile(
    r"(?P<path>[\w@+\-]*[./][\w@+.\-/]*|Makefile|Dockerfile|Gemfile|Rakefile|Procfile|Justfile|justfile)"
    r":(?P<line>\d+)(?:-(?P<end>\d+))?"
)
CODE_STATUSES = {"HANDLED", "PARTIAL", "UNHANDLED"}
LATE_VERIFICATIONS = {"upheld", "overturned"}
PROBE_VERIFICATIONS = {"probe-confirmed", "probe-not-reproduced", "probe-inconclusive"}


def priority_of(case: dict) -> str | None:
    return MATRIX.get(case.get("severity"), {}).get(case.get("likelihood"))


def sort_key(case: dict) -> tuple:
    def rank(seq, value):
        return seq.index(value) if value in seq else len(seq)

    num = re.sub(r"\D", "", str(case.get("id", ""))) or "0"
    return (rank(PRIORITIES, priority_of(case)), rank(SEVERITIES, case.get("severity")),
            rank(LIKELIHOODS, case.get("likelihood")), int(num))


def norm(text: str) -> str:
    return re.sub(r"\W+", " ", str(text).lower()).strip()


def fill(doc: dict) -> int:
    """Compute priorities, sort, and at quick level trim to the cap. Returns the number trimmed."""
    cases = doc.get("cases", [])
    if not isinstance(cases, list) or not all(isinstance(c, dict) for c in cases):
        return 0  # check() reports the malformed entries; nothing safe to fill
    for case in cases:
        case["priority"] = priority_of(case)
    cases.sort(key=sort_key)
    trimmed = 0
    if doc.get("target", {}).get("level") == "quick" and len(cases) > QUICK_CAP:
        trimmed = len(cases) - QUICK_CAP
        del cases[QUICK_CAP:]
        doc["trimmed"] = int(doc.get("trimmed", 0)) + trimmed
    return trimmed


def check(doc: dict, *, filled: bool, final: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if doc.get("schema") != "edge-cases/1":
        errors.append('schema: must be "edge-cases/1"')

    target = doc.get("target") or {}
    kind, level = target.get("kind"), target.get("level")
    if kind not in KINDS:
        errors.append(f"target.kind: {kind!r} is not one of {sorted(KINDS)}")
    if level not in LEVELS:
        errors.append(f"target.level: {level!r} is not one of {LEVELS}")
    for key in ("spec", "slug"):
        if not isinstance(target.get(key), str) or not target.get(key):
            errors.append(f"target.{key}: required")
    if not isinstance(target.get("grounded"), bool):
        errors.append("target.grounded: must be true or false")
    if target.get("built") not in (True, False, None):
        errors.append("target.built: must be true, false, or null")
    if kind == "feature" and target.get("built") is None:
        errors.append("target.built: a feature target must be settled to true or false in pre-flight")
    if "degraded_from" in target:
        if target.get("degraded_from") != "prove" or level != "deep" or not target.get("degraded_reason"):
            errors.append("target.degraded_from: only prove degrades, to level deep, with a degraded_reason")
    for key in ("trimmed", "dropped"):
        if key in doc and (not isinstance(doc[key], int) or doc[key] < 0):
            errors.append(f"{key}: must be a non-negative integer")
    grounded = target.get("grounded") is True and target.get("built") is not False
    code_target = grounded and kind in ("feature", "changes")
    late = level in ("deep", "prove")

    lenses = doc.get("lenses") or {}
    applied = lenses.get("applied")
    if not isinstance(applied, list):
        errors.append("lenses.applied: required list")
        applied = []
    for lens in applied:
        if lens not in LENSES or lens == "interaction":
            errors.append(f"lenses.applied: {lens!r} is not a first-pass lens")
    for item in lenses.get("skipped", []) if isinstance(lenses.get("skipped"), list) else []:
        if not isinstance(item, dict) or item.get("id") not in LENSES or not item.get("reason"):
            errors.append(f"lenses.skipped: {item!r} needs a valid id and a reason")
    if not isinstance(lenses.get("skipped"), list):
        errors.append("lenses.skipped: required list (may be empty)")

    cases = doc.get("cases")
    if not isinstance(cases, list):
        errors.append("cases: required list")
        return errors, warnings
    if not cases:
        warnings.append("no cases: say why in the report (a trivial target is a legitimate result)")
    if level == "quick" and len(cases) > QUICK_CAP:
        errors.append(f"quick level allows at most {QUICK_CAP} cases, found {len(cases)} (run --fill to trim)")

    ids = [c.get("id") for c in cases if isinstance(c, dict)]
    dup_ids = [i for i, n in Counter(ids).items() if n > 1]
    for i in dup_ids:
        errors.append(f"{i}: duplicate id")
    id_set = set(ids)
    for item in doc.get("dismissed", []) or []:
        if not isinstance(item, dict) or not all(str(item.get(k) or "").strip() for k in ("id", "title", "reason")):
            errors.append(f"dismissed: {item!r} needs id, title and reason")
        elif item.get("id") in id_set:
            errors.append(f"{item.get('id')}: is both a case and dismissed")

    seen_triggers: dict[str, str] = {}
    for idx, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"cases[{idx}]: not an object")
            continue
        cid = case.get("id") or f"cases[{idx}]"
        where = str(cid)

        for key in REQUIRED:
            value = case.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{where}: {key} is required")
        if not isinstance(case.get("current_evidence"), str):
            errors.append(f"{where}: current_evidence is required (an empty string only for N/A)")
        if not CASE_ID.match(str(case.get("id", ""))):
            errors.append(f"{where}: id must look like EC-01")

        lens = case.get("lens")
        if lens not in LENSES:
            errors.append(f"{where}: lens {lens!r} is not one of {LENSES}")
        elif lens == "interaction":
            if not late:
                errors.append(f"{where}: interaction cases exist only at deep and prove")
            related = case.get("related") or []
            if len({r for r in related if r in id_set and r != cid}) < 2:
                errors.append(f"{where}: an interaction case needs related: [two existing case ids]")
        elif lens not in applied:
            errors.append(f"{where}: lens {lens!r} is not in lenses.applied")
        for rel in case.get("related") or []:
            if rel not in id_set:
                errors.append(f"{where}: related id {rel!r} does not exist")

        source, decision = case.get("expected_source"), case.get("decision")
        evidence = str(case.get("expected_evidence") or "")
        if source not in SOURCES:
            errors.append(f"{where}: expected_source {source!r} is not one of {sorted(SOURCES)}")
        elif source == "convention" and not LOCATION.search(evidence):
            errors.append(f"{where}: a convention source needs file:line in expected_evidence")
        alternatives = case.get("alternatives")
        if alternatives is not None and (not isinstance(alternatives, list)
                                         or not all(isinstance(a, str) and a.strip() for a in alternatives)):
            errors.append(f"{where}: alternatives must be a list of non-empty strings")
        if source == "proposed":
            if decision not in DECISIONS:
                errors.append(f"{where}: a proposed behavior needs decision in {sorted(DECISIONS)}")
            elif decision in ("decided", "open") and not str(case.get("decision_note") or "").strip():
                errors.append(f"{where}: decision {decision!r} needs a decision_note")
        elif source in ("spec", "convention") and decision is not None:
            errors.append(f"{where}: decision must be null for a {source} source")

        status, verification = case.get("current_status"), case.get("verification")
        current = str(case.get("current_evidence") or "")
        if status not in STATUSES:
            errors.append(f"{where}: current_status {status!r} is not one of {STATUSES}")
        elif not grounded and status != "N/A":
            errors.append(f"{where}: the target is not grounded or not built, so current_status must be N/A")
        elif code_target and status == "N/A":
            errors.append(f"{where}: a built code target needs a status (use UNKNOWN, not N/A)")
        if status in CODE_STATUSES and not LOCATION.search(current):
            errors.append(f"{where}: {status} needs file:line in current_evidence")
        if status == "UNKNOWN" and not current.strip():
            errors.append(f"{where}: UNKNOWN needs current_evidence saying why")

        if verification not in VERIFICATIONS:
            errors.append(f"{where}: verification {verification!r} is not one of {sorted(VERIFICATIONS)}")
        elif status == "N/A" and verification != "n/a":
            errors.append(f"{where}: an N/A status takes verification n/a")
        elif status != "N/A" and verification == "n/a":
            errors.append(f"{where}: verification n/a is only for an N/A status")
        elif verification in LATE_VERIFICATIONS and not late:
            errors.append(f"{where}: {verification} happens only at deep and prove")
        elif verification in PROBE_VERIFICATIONS and level != "prove":
            errors.append(f"{where}: {verification} happens only at prove")

        severity, likelihood = case.get("severity"), case.get("likelihood")
        if severity not in SEVERITIES:
            errors.append(f"{where}: severity {severity!r} is not one of {SEVERITIES}")
        if likelihood not in LIKELIHOODS:
            errors.append(f"{where}: likelihood {likelihood!r} is not one of {LIKELIHOODS}")
        expected_priority = priority_of(case)
        if not filled and expected_priority and case.get("priority") != expected_priority:
            errors.append(f"{where}: priority {case.get('priority')!r} should be {expected_priority} "
                          f"({severity} x {likelihood}); run --fill")

        unverified = (late and status in CODE_STATUSES and verification == "as-read"
                      and expected_priority in ("P0", "P1"))
        if unverified:
            msg = f"{where}: {expected_priority} {status} is still as-read at {level}; a skeptic must check it"
            (errors if final else warnings).append(msg)

        origin = case.get("origin")
        if kind == "changes" and origin not in ORIGINS:
            errors.append(f"{where}: a changes target needs origin introduced | pre-existing")
        elif kind != "changes" and origin is not None:
            errors.append(f"{where}: origin applies only to changes targets")

        trigger = norm(f"{case.get('given', '')} {case.get('when', '')}")
        if trigger and trigger in seen_triggers:
            warnings.append(f"{where}: same given/when as {seen_triggers[trigger]}; merge them?")
        elif trigger:
            seen_triggers[trigger] = where

    needed = sum(1 for c in cases if isinstance(c, dict) and c.get("decision") == "needed")
    if needed:
        warnings.append(f"{needed} expected behavior(s) still need a decision (shown as DECISION NEEDED)")
    if code_target:
        statused = [c for c in cases if isinstance(c, dict) and c.get("current_status") in STATUSES[:4]]
        unknown = sum(1 for c in statused if c.get("current_status") == "UNKNOWN")
        if statused and unknown / len(statused) > 0.3:
            warnings.append(f"{unknown}/{len(statused)} statuses are UNKNOWN: grounding is thin; say so in Coverage")
    return errors, warnings


def check_locations(doc: dict, repo: Path) -> list[str]:
    """Every code citation must name a real repo-relative file and a line inside it."""
    errors: list[str] = []
    line_counts: dict[str, int | None] = {}

    def lines_in(rel: str) -> int | None:
        if rel not in line_counts:
            path = (repo / rel)
            try:
                if path.is_file():
                    data = path.read_bytes()
                    line_counts[rel] = data.count(b"\n") + (0 if not data or data.endswith(b"\n") else 1)
                else:
                    line_counts[rel] = None
            except OSError:
                line_counts[rel] = None
        return line_counts[rel]

    for case in doc.get("cases", []):
        if not isinstance(case, dict):
            continue
        cited = [str(case.get("current_evidence") or "")]
        if case.get("expected_source") == "convention":
            cited.append(str(case.get("expected_evidence") or ""))
        for text in cited:
            for m in LOCATION.finditer(text):
                rel = m.group("path").removeprefix("./")
                last = int(m.group("end") or m.group("line"))
                count = lines_in(rel)
                if count is None:
                    errors.append(f"{case.get('id')}: cites {m.group(0)} but {rel} is not a file in the repo "
                                  "(paths are repo-relative)")
                elif int(m.group("line")) < 1 or last > count:
                    errors.append(f"{case.get('id')}: cites {m.group(0)} but {rel} has {count} line(s)")
    return errors


def settled(case: dict) -> bool:
    """The expected behavior is agreed: stated by a source, uncontested, or decided by the user."""
    return case.get("expected_source") in ("spec", "convention") or case.get("decision") in ("uncontested", "decided")


VERIFIED = {"upheld", "overturned", "probe-confirmed"}


def tally(doc: dict) -> dict:
    cases = [c for c in doc.get("cases", []) if isinstance(c, dict)]
    by = lambda key: dict(sorted(Counter(str(c.get(key)) for c in cases).items()))  # noqa: E731
    p01 = [c for c in cases if priority_of(c) in ("P0", "P1")]
    return {
        "target": doc.get("target", {}),
        "total": len(cases),
        "by_priority": {p: sum(1 for c in cases if priority_of(c) == p) for p in PRIORITIES},
        "by_status": {s: sum(1 for c in cases if c.get("current_status") == s) for s in STATUSES},
        "by_lens": by("lens"),
        "by_source": by("expected_source"),
        "decisions": {d: sum(1 for c in cases if c.get("decision") == d) for d in sorted(DECISIONS)},
        "verification": by("verification"),
        "by_origin": by("origin") if (doc.get("target") or {}).get("kind") == "changes" else {},
        # A defect: P0/P1, the code misses an expectation that is agreed. An undecided proposal is not one.
        "defects_p0_p1": [c["id"] for c in p01 if c.get("current_status") in ("UNHANDLED", "PARTIAL") and settled(c)],
        "verified_defects_p0_p1": [c["id"] for c in p01 if c.get("current_status") in ("UNHANDLED", "PARTIAL")
                                   and settled(c) and c.get("verification") in VERIFIED],
        "confirmed_p0_p1": [c["id"] for c in p01 if c.get("verification") == "probe-confirmed"],
        "undecided_unhandled_p0_p1": [c["id"] for c in p01 if c.get("current_status") in ("UNHANDLED", "PARTIAL")
                                      and not settled(c)],
        "dismissed": len(doc.get("dismissed", []) or []),
        "trimmed": int(doc.get("trimmed", 0)),
        "dropped": int(doc.get("dropped", 0)),
        "lenses_applied": (doc.get("lenses") or {}).get("applied", []),
        "lenses_skipped": [s.get("id") for s in (doc.get("lenses") or {}).get("skipped", []) if isinstance(s, dict)],
    }


def cell(text: str, limit: int = 110) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip().replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def markdown(doc: dict) -> str:
    rows = [
        "| ID | P | Lens | Case | Expected (source) | Current | Verified |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for c in sorted((c for c in doc.get("cases", []) if isinstance(c, dict)), key=sort_key):
        if c.get("decision") == "needed":
            expected = f"**DECISION NEEDED** — proposed: {cell(c.get('then', ''), 80)}"
        elif c.get("decision") == "open":
            expected = f"**OPEN** — {cell(c.get('then', ''), 80)}"
        else:
            expected = f"{cell(c.get('then', ''), 90)} ({c.get('expected_source')})"
        status = c.get("current_status", "")
        loc = LOCATION.search(str(c.get("current_evidence") or ""))
        current = "—" if status == "N/A" else f"{status}" + (f" `{loc.group(0)}`" if loc else "")
        rows.append(
            f"| {c.get('id')} | {priority_of(c) or '?'} | {c.get('lens')} | {cell(c.get('title', ''), 80)} "
            f"| {expected} | {current} | {c.get('verification')} |"
        )
    return "\n".join(rows) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cases", help="path to cases.json")
    ap.add_argument("--fill", action="store_true", help="compute priorities, sort, trim at quick; write back if valid")
    ap.add_argument("--final", action="store_true", help="report-time check: unverified P0/P1 at deep/prove is an error")
    ap.add_argument("--markdown", metavar="OUT", help="write the case matrix table to OUT ('-' for stdout)")
    ap.add_argument("--summary", action="store_true", help="print tallies as JSON")
    ap.add_argument("--repo", metavar="DIR", help="check that every cited code file:line exists under DIR")
    args = ap.parse_args(argv)

    path = Path(args.cases)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"check_cases: cannot read {path}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(doc, dict):
        print(f"check_cases: {path} must hold a JSON object", file=sys.stderr)
        return 2

    trimmed = fill(doc) if args.fill else 0
    errors, warnings = check(doc, filled=args.fill, final=args.final)
    if args.repo:
        errors += check_locations(doc, Path(args.repo))

    out = sys.stderr if args.summary or args.markdown == "-" else sys.stdout
    for msg in errors:
        print(f"FAIL  {msg}", file=out)
    for msg in warnings:
        print(f"warn  {msg}", file=out)
    if errors:
        print(f"check_cases: {len(errors)} error(s); nothing written", file=out)
        return 1

    if args.fill:
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    t = tally(doc)
    p = t["by_priority"]
    print(f"  ok  {t['total']} cases (P0 {p['P0']} · P1 {p['P1']} · P2 {p['P2']} · P3 {p['P3']})"
          + (f"; trimmed {trimmed} at quick" if trimmed else "")
          + ("; priorities filled" if args.fill else ""), file=out)

    if args.markdown:
        table = markdown(doc)
        if args.markdown == "-":
            sys.stdout.write(table)
        else:
            Path(args.markdown).write_text(table, encoding="utf-8")
    if args.summary:
        json.dump(t, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
