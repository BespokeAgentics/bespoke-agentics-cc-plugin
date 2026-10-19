#!/usr/bin/env python3
"""Assemble a micro-interactions prototype from the skill's runtime, template and a project folder.

This is the mechanical half of the micro-interactions skill. The model writes the
project-specific files (page.json, tokens.css, stage.css, data.js, demos*.js, walk.js);
this script copies the shared runtime next to them, fills the page template from
page.json, and checks the result for the defects that recur:

  - unfilled {{PLACEHOLDERS}} in the page
  - a missing project file, or a demos file that page.json lists but does not exist
  - data.js ideas that break the contract (unknown flow or motion, duplicate id,
    impact/effort outside 1-3, a missing field, no first batch)
  - an idea with no demo, or a demo with no idea
  - raw '<' in data.js text, which renders as HTML (escape it as &lt;)

Stdlib only. It does not run JavaScript: it reads data.js and the demo files as text.
A clean check is necessary, not sufficient; the browser pass in the skill still runs.

Usage:
    python3 build.py <project-dir>            # build into <project-dir>, then check
    python3 build.py <project-dir> --check    # check only, write nothing
    python3 build.py <project-dir> --json     # print the check report as JSON

Exit code 0 when the check is clean, 1 when it found problems, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
RUNTIME = SKILL / "assets" / "runtime"
TEMPLATE = SKILL / "assets" / "template" / "index.html"

REQUIRED = ["page.json", "tokens.css", "stage.css", "data.js", "walk.js"]
# A "<placeholder>" from the starter templates; real HTML tags (<b>, <code>, <span …>) do not match.
TEMPLATE_TEXT = r"<(?:[A-Z][^<>]*|≈[^<>]*|N[ >][^<>]*|(?:the|one|which|what|relative|plan|where|files|why|function|flow|project|duration|:port)\b[^<>]*)>"
IDEA_FIELDS = ["id", "flow", "prims", "impact", "effort", "title", "why", "trigger", "moves", "reduced", "where"]
PAGE_KEYS = {
    "TITLE": "title",
    "PRODUCT": "product",
    "H1": "h1",
    "LEDE": "lede",
    "ESTIMATE": "estimate",
    "READ_FROM": "read_from",
    "VOCAB_H2": "vocab_h2",
    "VOCAB_P": "vocab_p",
    "WALK_H2": "walk_h2",
    "WALK_P": "walk_p",
    "START_P": "start_p",
    "GUARD_P": "guard_p",
    "FOOTER": "footer",
    "PLAN_HREF": "plan_href",
}


def bullets(items: list[str]) -> str:
    return "\n".join(f"          <li>{x}</li>" for x in items)


def fill(page: dict, out: Path) -> str:
    html = TEMPLATE.read_text()
    values = {k: page.get(v, "") for k, v in PAGE_KEYS.items()}
    values["RUNTIME"] = "runtime"
    values["V"] = str(int(time.time()))
    values["BRAND_MARK"] = page.get("brand_mark_html", "")
    fav = page.get("favicon")
    # Without a declared icon the browser requests /favicon.ico and logs a 404 the browser check then reports.
    values["FAVICON_LINK"] = f'<link rel="icon" href="{fav}">' if fav else '<link rel="icon" href="data:,">'
    values["GUARD_NEVER"] = bullets(page.get("guard_never", []))
    values["GUARD_ALWAYS"] = bullets(page.get("guard_always", []))
    demos = page.get("demo_files") or sorted(p.name for p in out.glob("demos*.js"))
    values["DEMO_SCRIPTS"] = "\n".join(f'<script src="{d}?v={values["V"]}"></script>' for d in demos)
    for key, val in values.items():
        html = html.replace("{{" + key + "}}", str(val))
    return html


# ---- checks (text-level; no JS engine) ---------------------------------------------------------

def js_array(src: str, name: str) -> str | None:
    """Return the text of `MI.<name> = [ ... ];` with brackets balanced, or None."""
    m = re.search(r"MI\." + name + r"\s*=\s*\[", src)
    if not m:
        return None
    i, depth, quote = m.end() - 1, 0, None
    while i < len(src):
        c = src[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return src[m.end():i]
        i += 1
    return None


def objects(arr: str) -> list[str]:
    """Split the top-level { ... } objects of an array literal."""
    out, depth, start, quote, i = [], 0, None, None, 0
    while i < len(arr):
        c = arr[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
        elif c == "{":
            if depth == 0:
                start = i
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and start is not None:
                out.append(arr[start:i + 1])
        i += 1
    return out


def field(obj: str, key: str) -> str | None:
    m = re.search(r"\b" + key + r"\s*:\s*(\"(?:[^\"\\]|\\.)*\"|\[[^\]]*\]|-?\d+|true|false)", obj)
    return m.group(1) if m else None


def check(out: Path) -> dict:
    problems: list[str] = []
    notes: list[str] = []

    for name in REQUIRED:
        if not (out / name).exists():
            problems.append(f"missing project file: {name}")
    if problems:
        return {"ok": False, "problems": problems, "notes": notes}

    page = json.loads((out / "page.json").read_text())
    for d in page.get("demo_files", []):
        if not (out / d).exists():
            problems.append(f"page.json lists {d}, which does not exist")

    index = out / "index.html"
    if index.exists():
        left = sorted(set(re.findall(r"\{\{([A-Z_]+)\}\}", index.read_text())))
        if left:
            problems.append("unfilled placeholders in index.html: " + ", ".join(left))
    for key in ("h1", "lede", "product", "title"):
        if not page.get(key):
            problems.append(f"page.json has no '{key}'")
    # Starter text left in from assets/template/page.json: "<Product>", "<N> motions", "<≈ N days…>".
    for key, val in page.items():
        for v in (val if isinstance(val, list) else [val]):
            if isinstance(v, str) and re.search(TEMPLATE_TEXT, v):
                problems.append(f"page.json '{key}' still has template text: {re.search(TEMPLATE_TEXT, v).group(0)}")

    data = (out / "data.js").read_text()
    prims_src, flows_src, ideas_src = js_array(data, "prims"), js_array(data, "flows"), js_array(data, "ideas")
    if not (prims_src and flows_src and ideas_src):
        problems.append("data.js must set MI.prims, MI.flows and MI.ideas as array literals")
        return {"ok": False, "problems": problems, "notes": notes}
    for kind, src in (("motion", prims_src), ("flow", flows_src)):
        for o in objects(src):
            if re.search(r"<(?!/?(b|u|code)>)[a-zA-Z/]", o):
                problems.append(f"{kind} {field(o, 'id') or '?'}: raw '<' in text renders as HTML; write &lt;")
    if re.search(TEMPLATE_TEXT, data):
        problems.append("data.js still has template text: " + re.search(TEMPLATE_TEXT, data).group(0))
    prim_ids = [json.loads(field(o, "id")) for o in objects(prims_src) if field(o, "id")]
    flow_ids = [json.loads(field(o, "id")) for o in objects(flows_src) if field(o, "id")]
    ideas = objects(ideas_src)
    ids: list[str] = []
    first = 0
    for o in ideas:
        iid = field(o, "id")
        label = json.loads(iid) if iid else "(no id)"
        for f in IDEA_FIELDS:
            if field(o, f) is None:
                problems.append(f"idea {label}: missing '{f}'")
        if iid:
            ids.append(label)
        fl = field(o, "flow")
        if fl and json.loads(fl) not in flow_ids:
            problems.append(f"idea {label}: flow {fl} is not in MI.flows")
        pr = field(o, "prims")
        if pr:
            for p in re.findall(r"\"([^\"]+)\"", pr):
                if p not in prim_ids:
                    problems.append(f"idea {label}: motion \"{p}\" is not in MI.prims")
        for f in ("impact", "effort"):
            v = field(o, f)
            if v and not (v.isdigit() and 1 <= int(v) <= 3):
                problems.append(f"idea {label}: {f} must be 1, 2 or 3 (got {v})")
        if field(o, "first") == "true":
            first += 1
        if re.search(r"<(?!/?(b|u|code)>)[a-zA-Z/]", o):
            problems.append(f"idea {label}: raw '<' in text renders as HTML; write &lt;")
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        problems.append("duplicate idea ids: " + ", ".join(dupes))
    if not first:
        problems.append("no idea is marked first: true; the page needs a first batch")

    demo_src = "\n".join(p.read_text() for p in sorted(out.glob("demos*.js")))
    defined = set(re.findall(r"\bD\.([A-Za-z]+\d+)\s*=", demo_src)) | set(re.findall(r"MI\.demos\.([A-Za-z]+\d+)\s*=", demo_src))
    prim_demos = set(re.findall(r"\bP\.([a-z][\w-]*)\s*=", demo_src)) | set(re.findall(r"MI\.primDemos\.([a-z][\w-]*)\s*=", demo_src))
    for i in dict.fromkeys(ids):
        if i not in defined:
            problems.append(f"idea {i} has no demo (MI.demos.{i})")
    for d in sorted(defined - set(ids)):
        problems.append(f"demo {d} has no idea in data.js")
    for p in prim_ids:
        if p not in prim_demos:
            problems.append(f"motion '{p}' has no demo (MI.primDemos.{p})")
    for p in sorted(prim_demos - set(prim_ids)):
        problems.append(f"motion demo '{p}' has no motion in MI.prims")

    order_src = js_array(data, "firstOrder")
    if order_src is None:
        notes.append("MI.firstOrder not set: the first batch is listed in data order")
    else:
        for oid in re.findall(r"\[\s*\"([^\"]+)\"", order_src):
            if oid not in ids:
                problems.append(f"MI.firstOrder names {oid}, which is not in MI.ideas")

    walk = (out / "walk.js").read_text()
    if "MI.walk" not in walk:
        problems.append("walk.js must set MI.walk (see runtime/mi-walk.js for the contract)")
    for ref in set(re.findall(r"ids:\s*\[([^\]]*)\]", walk)):
        for i in re.findall(r"\"([^\"]+)\"", ref):
            if i not in ids:
                problems.append(f"walk.js step names idea {i}, which is not in data.js")

    notes.append(f"{len(ids)} ideas over {len(flow_ids)} flows, {len(prim_ids)} motions, first batch {first}")
    return {"ok": not problems, "problems": problems, "notes": notes}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("project", type=Path, help="folder holding page.json, tokens.css, stage.css, data.js, demos*.js, walk.js")
    ap.add_argument("--check", action="store_true", help="check only; write nothing")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    a = ap.parse_args()
    out = a.project.resolve()
    if not out.is_dir():
        print(f"not a folder: {out}", file=sys.stderr)
        return 2

    if not a.check:
        missing = [n for n in REQUIRED if not (out / n).exists()]
        if missing:
            print("cannot build, missing: " + ", ".join(missing), file=sys.stderr)
            return 2
        dest = out / "runtime"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(RUNTIME, dest)
        page = json.loads((out / "page.json").read_text())
        (out / "index.html").write_text(fill(page, out))

    report = check(out)
    if a.json:
        print(json.dumps(report, indent=2))
    else:
        for n in report["notes"]:
            print("  " + n)
        for p in report["problems"]:
            print("  FAIL " + p)
        print("check: " + ("clean" if report["ok"] else f"{len(report['problems'])} problem(s)"))
        if not a.check and report["ok"]:
            print(f"open: {out / 'index.html'} (serve the folder over http so fonts and images load)")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
