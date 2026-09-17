#!/usr/bin/env python3
"""project-ontology engine — an enforceable, dot-notated ontology over a project's wiki (or docs).

Vendored into <project>/.claude/ontology/ontology.py by the project-ontology skill (/ontology:init).
Standard library only, and deliberately never PyYAML: a hook that passes on one machine and blocks on
another is worse than no hook. One file on purpose — the PreToolUse / PostToolUse hooks, the CLI,
wiki-lint and project-db all run the SAME rules from here, so the write hook and the database can
never disagree about what is a violation.

Pages keep plain frontmatter values (`severity: critical`). The ontology file declares which plain
values are legal as dot-notated terms (`gap.severity.critical`), with a lifecycle
(proposed → approved → deprecated). Page ids are derived from paths, never written into pages.

Subcommands
  init       --scan: mine the vault into .claude/ontology/init-report.json
             --write [--decisions f.json]: build ontology.yaml from the report, render, install
  install    (re)vendor engine + hooks, merge settings.json, CLAUDE.md block, .gitignore
  check      [paths…] | --all | --changed-since <ref>   exit 1 on strict violations
  hook       pre | post | bash — Claude Code hook entry points (hook JSON on stdin)
  propose    <id> --label … --definition …   register a term (status: proposed) — any agent
  approve    <id>… --by <human>               proposed → approved — a human gate
  deprecate  <id> --reason … --by <human> [--replaced-by <id>]
  apply      [--dry-run] [paths…]             rewrite aliases, variants, deprecated values, noncanonical links
  render     ONTOLOGY.md [--templates: sync `key: # binding: a|b|c` comments in page templates]
  status     counts, policy, open violations — JSON by default, --banner for the SessionStart hook
  ls         [--prefix gap.] [--status proposed] [--kind vocab]
"""
from __future__ import annotations

import argparse
import difflib
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

API_VERSION = 1
ENGINE_VERSION = "1.0.0"
ONTO_DIR_REL = ".claude/ontology"
CONFIG_REL = f"{ONTO_DIR_REL}/config.json"
STATE_REL = f"{ONTO_DIR_REL}/state.json"
REPORT_REL = f"{ONTO_DIR_REL}/init-report.json"
GUARD_HOOK_REL = ".claude/hooks/ontology-guard.sh"
CONTEXT_HOOK_REL = ".claude/hooks/ontology-context.sh"
SENTINEL_OPEN = "<!-- project-ontology:managed -->"
SENTINEL_CLOSE = "<!-- /project-ontology:managed -->"
ENGINE_CMD = "python3 .claude/ontology/ontology.py"

SECTIONS = ("types", "vocabularies", "entities", "relations", "tags")
KIND_BY_SECTION = {"types": "type", "vocabularies": "vocab", "entities": "entity", "relations": "relation", "tags": "tag"}
SECTION_BY_KIND = {v: k for k, v in KIND_BY_SECTION.items()}
STATUSES = ("proposed", "approved", "deprecated")
POLICIES = ("strict", "warn", "off")
FAMILIES = ("type", "vocab", "entity", "tag", "link", "relation", "id")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)*$")
EMOJI_LEAVES = {"🟢": "ootb", "🔵": "config", "🟡": "custom-dev", "🔴": "gap", "⚪": "tbd", "🟣": "third-party"}
DEFAULT_SCOPE_FOLDERS = OrderedDict([("clients", "client"), ("projects", "project"), ("platforms", "platform"),
                                     ("teams", "team"), ("domains", "domain"), ("products", "product"), ("orgs", "org")])
DEFAULT_FOLDER_NOTES = ["overview", "readme", "index"]
DEFAULT_IGNORE_TYPES = ["index", "log", "lint-report"]
DEFAULT_LINK_EXCLUDE = ["_schema/templates/*"]
MULTI_KEYS = {"tags", "sources"}  # never relation candidates: tags are their own kind, sources are citations
TERM_ATTR_ORDER = ("label", "value", "definition", "status", "aliases", "proposed-aliases", "domain", "range",
                   "replaced-by", "reason", "since", "source", "proposed-by", "approved-by", "approved-on",
                   "deprecated-by", "deprecated-on")


# ----------------------------------------------------------------------------- helpers

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return now_iso()[:10]


def die(msg: str, code: int = 2) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def slugify(s) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(s).strip().lower())).strip("-")


def norm(s) -> str:
    """Spelling-insensitive key: `Boston Beer Company` ≡ `boston-beer-company`, `p1` ≡ `P1`."""
    return slugify(s) or str(s).strip().casefold()


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def as_list(v) -> list:
    if v is None or v == "":
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


def actor() -> str:
    return os.environ.get("ONTOLOGY_ACTOR") or os.environ.get("USER") or "unknown"


def find_root(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / CONFIG_REL).exists():
            return cand
    return p


def rel_posix(path: Path, root: Path) -> str | None:
    """Project-relative posix path. Pure string work when the path is already under the root (the walk
    case — a realpath syscall per file made a 5,000-page vault walk ~10x slower); resolve() otherwise."""
    s, r = str(path), str(root)
    if s.startswith(r + os.sep) and ".." not in Path(s[len(r) + 1:]).parts:
        return s[len(r) + 1:].replace(os.sep, "/")
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return None


# ----------------------------------------------------------------------------- page frontmatter (parity with project-db)
#
# The parser below is the project-db subset parser (same regexes, same scalar rules), so the database's
# page_fields and this engine's checks read identical values. test_ontology.py pins the parity.

FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
KEY_LINE_RE = re.compile(r"^([A-Za-z0-9_\-]+):(.*)$")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
CODE_FENCE_RE = re.compile(r"^[ \t]*(```|~~~)[^\n]*\n.*?^[ \t]*\1[ \t]*$", re.M | re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def split_frontmatter(text: str) -> tuple[str | None, str]:
    m = FM_RE.match(text)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def _scalar(raw: str):
    s = raw.strip()
    if s == "" or s in ("null", "~"):
        return None
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    if s.startswith("[[") and s.endswith("]]"):
        return s
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        items, buf, depth, q = [], "", 0, None
        for ch in inner:
            if q:
                buf += ch
                if ch == q:
                    q = None
                continue
            if ch in "\"'":
                q = ch
                buf += ch
                continue
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            if ch == "," and depth == 0:
                items.append(_scalar(buf))
                buf = ""
            else:
                buf += ch
        if buf.strip():
            items.append(_scalar(buf))
        return items
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if re.fullmatch(r"-?\d+", s):
        try:
            return int(s)
        except ValueError:
            return s
    if re.fullmatch(r"-?\d+\.\d+", s):
        try:
            return float(s)
        except ValueError:
            return s
    return s


def _strip_comment(raw: str) -> tuple[str, str | None]:
    """Split `value # comment`. A '#' inside quotes or [[...]] is not a comment."""
    q, depth = None, 0
    for i, ch in enumerate(raw):
        if q:
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == "#" and depth == 0 and (i == 0 or raw[i - 1] in " \t"):
            return raw[:i].rstrip(), raw[i + 1:].strip()
    return raw, None


def parse_frontmatter(fm_text: str) -> tuple[dict, dict]:
    """(data, docs): the YAML subset wiki frontmatter uses; docs maps key → trailing `# comment`.
    Block lists may be indented or at the key's own indent (`tags:` / `- a`) — both are valid YAML."""
    data: dict = {}
    docs: dict = {}
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        m = KEY_LINE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2)
        val_raw, comment = _strip_comment(rest)
        if comment:
            docs[key] = comment
        if val_raw.strip() == "":
            items, mapping, j = [], {}, i + 1
            while j < len(lines):
                ln = lines[j]
                if ln.strip() == "":
                    j += 1
                    continue
                if ln.startswith((" ", "\t")):
                    sub = ln.strip()
                    if sub.startswith("- "):
                        v, _ = _strip_comment(sub[2:])
                        items.append(_scalar(v))
                    elif sub and ":" in sub and not sub.startswith("-"):
                        k2, v2 = sub.split(":", 1)
                        v2, _ = _strip_comment(v2)
                        mapping[k2.strip()] = _scalar(v2)
                    j += 1
                    continue
                if ln.startswith("- ") and not mapping:
                    v, _ = _strip_comment(ln[2:])
                    items.append(_scalar(v))
                    j += 1
                    continue
                break
            data[key] = items if items else (mapping if mapping else None)
            i = j
            continue
        data[key] = _scalar(val_raw)
        i += 1
    return data, docs


def _unquote(tok: str) -> str:
    t = tok.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        return t[1:-1]
    return t


def _inline_list_spans(tok: str) -> list[tuple[int, int, str]]:
    """(start, end, raw) of each item of an inline `[a, "b", c]` list, offsets relative to tok —
    split exactly the way _scalar splits (quotes and nested brackets respected)."""
    out = []
    inner_start = 1
    buf_start, depth, q = inner_start, 0, None
    end = len(tok) - 1
    i = inner_start
    while i < end:
        ch = tok[i]
        if q:
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == "," and depth == 0:
            out.append((buf_start, i))
            buf_start = i + 1
        i += 1
    out.append((buf_start, end))
    spans = []
    for s, e in out:
        piece = tok[s:e]
        lead = len(piece) - len(piece.lstrip())
        stripped = piece.strip()
        if stripped:
            spans.append((s + lead, s + lead + len(stripped), stripped))
    return spans


def frontmatter_items(text: str) -> tuple[dict | None, list[dict], int]:
    """(data, items, body_offset). items: one per scalar value token in the frontmatter —
    {key, index, start, end, raw, line} with absolute character offsets into `text` (what `apply`
    rewrites) and 1-based line numbers (what messages cite). data is None when there is no frontmatter."""
    m = FM_RE.match(text)
    if not m:
        return None, [], 0
    fm_text = m.group(1)
    base = m.start(1)
    data, _docs = parse_frontmatter(fm_text)
    line0 = text[:base].count("\n")
    lines = fm_text.split("\n")
    offs, pos = [], 0
    for ln in lines:
        offs.append(pos)
        pos += len(ln) + 1
    items: list[dict] = []

    def add(key, idx, start, raw, lineno):
        items.append({"key": key, "index": idx, "start": start, "end": start + len(raw), "raw": raw, "line": lineno})

    i = 0
    while i < len(lines):
        ln = lines[i].rstrip("\r")
        km = KEY_LINE_RE.match(ln)
        if not km:
            i += 1
            continue
        key = km.group(1)
        rest_at = len(key) + 1
        val_raw, _c = _strip_comment(ln[rest_at:])
        if val_raw.strip() == "":
            j, idx, mapping = i + 1, 0, False
            while j < len(lines):
                l2 = lines[j].rstrip("\r")
                if l2.strip() == "":
                    j += 1
                    continue
                if l2.startswith((" ", "\t")):
                    s = l2.lstrip(" \t")
                    if s.startswith("- "):
                        at = len(l2) - len(s) + 2
                        v, _ = _strip_comment(l2[at:])
                        lead = len(v) - len(v.lstrip())
                        if v.strip():
                            add(key, idx, base + offs[j] + at + lead, v.strip(), line0 + j + 1)
                        idx += 1
                    elif s and ":" in s and not s.startswith("-"):
                        mapping = True
                    j += 1
                    continue
                if l2.startswith("- ") and not mapping:
                    v, _ = _strip_comment(l2[2:])
                    lead = len(v) - len(v.lstrip())
                    if v.strip():
                        add(key, idx, base + offs[j] + 2 + lead, v.strip(), line0 + j + 1)
                    idx += 1
                    j += 1
                    continue
                break
            i = j
            continue
        lead = len(val_raw) - len(val_raw.lstrip())
        tok = val_raw.strip()
        start = base + offs[i] + rest_at + lead
        if tok.startswith("[") and not tok.startswith("[[") and tok.endswith("]"):
            for n, (s, e, raw) in enumerate(_inline_list_spans(tok)):
                add(key, n, start + s, raw, line0 + i + 1)
        else:
            add(key, 0, start, tok, line0 + i + 1)
        i += 1
    return data, items, m.end()


def split_comma_tokens(raw: str) -> list[tuple[int, int, str]]:
    """`a, b, c` (tags written as one string) → spans of each part, relative to raw."""
    out, start, q = [], 0, None
    for i, ch in enumerate(raw + ","):
        if q:
            if ch == q:
                q = None
            continue
        if ch in "\"'" and i < len(raw):
            q = ch
            continue
        if ch == ",":
            piece = raw[start:i]
            lead = len(piece) - len(piece.lstrip())
            if piece.strip():
                out.append((start + lead, start + lead + len(piece.strip()), piece.strip()))
            start = i + 1
    return out


def visible_body(body: str) -> str:
    """What a reader sees as prose: HTML comments, fenced code and inline code removed (links inside
    them are not links). Replacements keep newlines so line numbers stay true."""
    body = HTML_COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), body)
    body = CODE_FENCE_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), body)
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), body)


def page_title(text: str, fallback: str) -> str:
    fm, body = split_frontmatter(text)
    for line in body.splitlines():
        m = HEADING_RE.match(line.strip())
        if m and len(m.group(1)) == 1:
            return m.group(2).strip()
    if fm is not None:
        data, _ = parse_frontmatter(fm)
        if data.get("title"):
            return str(data["title"])
    return fallback


# ----------------------------------------------------------------------------- ontology file (strict YAML subset)

class OntologyError(Exception):
    pass


_ONTO_KEY_RE = re.compile(r"""^("(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[A-Za-z0-9_.*/\-]+)[ \t]*:(?:[ \t]+(.*))?$""")


def _onto_unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1].replace("''", "'")
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return s[1:-1]
    return s


def _onto_split_list(inner: str, lineno: int) -> list[str]:
    items, buf, q, i = [], "", None, 0
    while i < len(inner):
        ch = inner[i]
        if q == "'":
            if ch == "'" and i + 1 < len(inner) and inner[i + 1] == "'":
                buf += "''"
                i += 2
                continue
            buf += ch
            if ch == "'":
                q = None
        elif q == '"':
            buf += ch
            if ch == "\\" and i + 1 < len(inner):
                buf += inner[i + 1]
                i += 2
                continue
            if ch == '"':
                q = None
        elif ch in "'\"":
            q = ch
            buf += ch
        elif ch == ",":
            items.append(buf)
            buf = ""
        else:
            buf += ch
        i += 1
    if q:
        raise OntologyError(f"line {lineno}: unterminated quote in list")
    if buf.strip():
        items.append(buf)
    return [_onto_unquote(x) for x in items if x.strip()]


def _onto_value(raw: str, lineno: int):
    s = raw.strip()
    if s == "" or s in ("~", "null"):
        return None
    if s[0] in "'\"":
        if len(s) < 2 or s[-1] != s[0]:
            raise OntologyError(f"line {lineno}: unterminated quoted string")
        return _onto_unquote(s)
    if s.startswith("[") and s.endswith("]"):
        return _onto_split_list(s[1:-1], lineno)
    if s.startswith(("{", "|", ">", "&", "*", "!")):
        raise OntologyError(f"line {lineno}: unsupported YAML construct `{s[:12]}` — the ontology file is a plain subset (mappings, scalars, [inline lists])")
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


def _onto_strip_comment(rest: str) -> str:
    q = None
    for i, ch in enumerate(rest):
        if q:
            if ch == q:
                q = None
            continue
        if ch in "'\"":
            q = ch
        elif ch == "#" and (i == 0 or rest[i - 1] in " \t"):
            return rest[:i].rstrip()
    return rest.rstrip()


def parse_onto_yaml(text: str) -> dict:
    """Nested block mappings (any consistent indent), scalars, quoted strings, [inline lists] and block
    lists. Anything else is an error with a line number — never a silent misread."""
    root: dict = {}
    stack: list[list] = [[-1, root, None, None]]  # [indent, container, parent, key]
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        body = line.rstrip()
        indent = len(body) - len(body.lstrip(" "))
        if body[indent:indent + 1] == "\t":
            raise OntologyError(f"line {lineno}: tabs are not allowed for indentation")
        content = body[indent:]
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        top = stack[-1]
        if content.startswith("- ") or content == "-":
            if isinstance(top[1], dict) and not top[1] and top[2] is not None:
                top[1] = []
                top[2][top[3]] = top[1]
            if not isinstance(top[1], list):
                raise OntologyError(f"line {lineno}: list item outside a list")
            top[1].append(_onto_value(_onto_strip_comment(content[2:]), lineno))
            continue
        m = _ONTO_KEY_RE.match(content)
        if not m:
            raise OntologyError(f"line {lineno}: expected `key: value`, got `{content[:40]}`")
        if not isinstance(top[1], dict):
            raise OntologyError(f"line {lineno}: mapping entry inside a list")
        key = _onto_unquote(m.group(1))
        rest = _onto_strip_comment(m.group(2) or "")
        if key in top[1]:
            raise OntologyError(f"line {lineno}: duplicate key `{key}`")
        if rest.strip() == "":
            child: dict = {}
            top[1][key] = child
            stack.append([indent, child, top[1], key])
        else:
            top[1][key] = _onto_value(rest, lineno)
    return root


_PLAIN_OK = re.compile(r"^[^\s'\"\[\]{},#&*!|>%@`?:-][^#\[\]{},'\"]*$")


def _onto_quote(s, in_list: bool = False) -> str:
    s = "" if s is None else str(s).replace("\r", " ").replace("\n", " ")
    needs = (not s or s != s.strip() or not _PLAIN_OK.match(s) or ": " in s or s.endswith(":")
             or s.lower() in ("true", "false", "yes", "no", "null", "~", "on", "off")
             or re.fullmatch(r"-?\d+(\.\d+)?", s) is not None or (in_list and "," in s))
    return "'" + s.replace("'", "''") + "'" if needs else s


def dump_onto_yaml(data: dict) -> str:
    """Deterministic writer. Comments are not preserved — rationale belongs in `definition` / `reason`."""
    out = ["# project-ontology — the controlled vocabulary for this project (dot-notated, enforced).",
           "# Change terms with /ontology:propose · /ontology:approve · /ontology:deprecate; approval is a human gate.",
           "# Rendered for reading: ONTOLOGY.md next to this file. This file is regenerated by the engine —",
           "# comments are not preserved; put rationale in `definition` or `reason`."]

    def emit(key, val, ind):
        pad = " " * ind
        k = _onto_quote(key) if not re.fullmatch(r"[A-Za-z0-9_.\-/]+", str(key)) else str(key)
        if isinstance(val, dict):
            if not val:
                out.append(f"{pad}{k}:")
                return
            out.append(f"{pad}{k}:")
            for kk, vv in val.items():
                emit(kk, vv, ind + 2)
        elif isinstance(val, (list, tuple)):
            out.append(f"{pad}{k}: [" + ", ".join(_onto_quote(x, True) for x in val) + "]")
        elif isinstance(val, bool):
            out.append(f"{pad}{k}: {'true' if val else 'false'}")
        elif isinstance(val, int):
            out.append(f"{pad}{k}: {val}")
        elif val is None:
            return
        else:
            out.append(f"{pad}{k}: {_onto_quote(val)}")

    for top in ("version", "name", "updated", "policy", "ids", "fields") + SECTIONS:
        if top not in data:
            continue
        val = data[top]
        if top in SECTIONS or top == "fields":
            out.append("")
        if isinstance(val, dict) and top in SECTIONS:
            out.append(f"{top}:")
            for tid, attrs in val.items():
                out.append(f"  {tid}:")
                for a in TERM_ATTR_ORDER:
                    if a in attrs and attrs[a] not in (None, "", []):
                        emit(a, attrs[a], 4)
                for a, v in attrs.items():
                    if a not in TERM_ATTR_ORDER and not a.startswith("_") and v not in (None, "", []):
                        emit(a, v, 4)
        else:
            emit(top, val, 0)
    for top, val in data.items():
        if top not in ("version", "name", "updated", "policy", "ids", "fields") + SECTIONS:
            emit(top, val, 0)
    return "\n".join(out) + "\n"


# ----------------------------------------------------------------------------- ontology model

def binding_key(type_part: str, field: str) -> str:
    return f"{type_part.strip().lower()}.{slugify(field)}"


def term_value(term: dict) -> str:
    if term.get("value") not in (None, ""):
        return str(term["value"])
    segs = term["_id"].split(".")
    if term["_kind"] == "tag":
        return "/".join(segs[1:])
    return segs[-1]


def term_parent(term: dict) -> str:
    return term["_id"].rsplit(".", 1)[0] if "." in term["_id"] else ""


class Ontology:
    def __init__(self, data: dict):
        self.data = data
        early_errors = []
        for sec in SECTIONS + ("fields",):
            v = data.get(sec)
            if not isinstance(v, dict):
                if v not in (None, "", []):
                    early_errors.append(f"{sec}: expected a mapping (`id:` entries), got {type(v).__name__}")
                data[sec] = OrderedDict()
        for sec in ("policy", "ids"):
            if data.get(sec) not in (None, "") and not isinstance(data.get(sec), dict):
                early_errors.append(f"{sec}: expected a mapping, got {type(data[sec]).__name__}")
                data[sec] = OrderedDict()
        pol = data.get("policy") if isinstance(data.get("policy"), dict) else {}
        self.policy_default = str(pol.get("default") or "strict")
        self.policy_proposed = str(pol.get("proposed") or "warn")
        self.approval = str(pol.get("approval") or "human")
        self.overrides = {str(k): str(v) for k, v in (pol.get("overrides") or {}).items()} if isinstance(pol.get("overrides"), dict) else {}
        ids = data.get("ids") if isinstance(data.get("ids"), dict) else {}
        sf = ids.get("scope-folders")
        self.scope_folders = OrderedDict((str(k), str(v)) for k, v in sf.items()) if isinstance(sf, dict) else OrderedDict()
        self.folder_notes = [str(x).lower() for x in as_list(ids.get("folder-notes"))] or list(DEFAULT_FOLDER_NOTES)
        self.ignore_types = [str(x).lower() for x in as_list(ids.get("ignore-types"))] if "ignore-types" in ids else list(DEFAULT_IGNORE_TYPES)
        self.terms: dict[str, dict] = OrderedDict()
        self.errors: list[str] = list(early_errors)
        for sec in SECTIONS:
            for tid, attrs in data[sec].items():
                if not isinstance(attrs, dict):
                    self.errors.append(f"{tid}: a term is a mapping of attributes (label, status, …)")
                t = dict(attrs) if isinstance(attrs, dict) else {}
                t["_id"], t["_kind"], t["_section"] = str(tid), KIND_BY_SECTION[sec], sec
                if t["_id"] in self.terms:
                    self.errors.append(f"{tid}: declared in both {self.terms[t['_id']]['_section']} and {sec}")
                self.terms[t["_id"]] = t
        self.fields: dict[str, dict] = OrderedDict()
        for k, spec in data["fields"].items():
            if "." not in str(k) or not isinstance(spec, dict):
                self.errors.append(f"fields.{k}: expected `<type>.<field>:` with a `kind:`")
                continue
            tp, f = str(k).split(".", 1)
            self.fields[binding_key(tp, f)] = dict(spec)
        self._domains: dict = {}
        self._validate()

    # --- lookups
    def type_values(self) -> set[str]:
        if not hasattr(self, "_type_values"):
            self._type_values = {term_value(t).lower() for t in self.terms.values() if t["_kind"] == "type"}
        return self._type_values

    def binding(self, ptype: str | None, field: str) -> tuple[str, dict] | None:
        if ptype:
            k = binding_key(ptype, field)
            if k in self.fields:
                return k, self.fields[k]
        k = binding_key("*", field)
        if k in self.fields:
            return k, self.fields[k]
        return None

    def domain_parent(self, bkey: str, spec: dict, ptype: str | None) -> tuple[str, str | None]:
        kind = spec.get("kind")
        if kind == "vocab":
            tp, f = bkey.split(".", 1)
            return "vocab", (f"{slugify(ptype)}.{f}" if tp == "*" and ptype else f"{tp}.{f}")
        if kind == "entity":
            return "entity", str(spec.get("namespace") or bkey.split(".", 1)[1])
        if kind == "tag":
            return "tag", None
        if kind == "type":
            return "type", "type"
        return str(kind), None

    def domain(self, kind: str, parent: str | None) -> dict:
        key = (kind, parent)
        if key not in self._domains:
            terms = [t for t in self.terms.values() if t["_kind"] == kind and (parent is None or term_parent(t) == parent)]
            idx: dict = {"terms": terms, "value": {}, "alias": {}, "palias": {}, "norm": {}}
            for t in terms:
                v = term_value(t)
                idx["value"].setdefault(v, []).append(t)
                names = [v]
                for a in as_list(t.get("aliases")):
                    idx["alias"].setdefault(str(a), []).append(t)
                    names.append(str(a))
                for a in as_list(t.get("proposed-aliases")):
                    idx["palias"].setdefault(str(a), []).append(t)
                    names.append(str(a))
                for n in {norm(x) for x in names}:
                    idx["norm"].setdefault(n, []).append(t)
            self._domains[key] = idx
        return self._domains[key]

    def match(self, kind: str, parent: str | None, value: str) -> tuple[dict | None, str | None]:
        d = self.domain(kind, parent)
        if value in d["value"]:
            return d["value"][value][0], "canonical"
        if value in d["alias"]:
            return d["alias"][value][0], "alias"
        if value in d["palias"]:
            return d["palias"][value][0], "proposed-alias"
        cands = list({t["_id"]: t for t in d["norm"].get(norm(value), [])}.values())
        if len(cands) == 1:
            return cands[0], "variant"
        return None, None

    def policy_for(self, rule: str, family: str, bkey: str | None, namespace: str | None) -> str:
        p = None
        for k in (bkey, namespace, family):
            if k and k in self.overrides:
                p = self.overrides[k]
                break
        p = p or self.policy_default
        if p not in POLICIES:
            p = "strict"
        if rule == "value-proposed":
            cap = self.policy_proposed if self.policy_proposed in POLICIES else "warn"
            order = {"off": 0, "warn": 1, "strict": 2}
            p = min(p, cap, key=lambda x: order[x])
        return p

    # --- validation
    def _validate(self) -> None:
        types = {t["_id"].split(".", 1)[1] for t in self.terms.values() if t["_kind"] == "type" and "." in t["_id"]}
        for tid, t in self.terms.items():
            kind, segs = t["_kind"], tid.split(".")
            if not ID_RE.match(tid):
                self.errors.append(f"{tid}: id must be dot-joined segments of a-z, 0-9 and '-'")
                continue
            if kind == "type" and (segs[0] != "type" or len(segs) != 2):
                self.errors.append(f"{tid}: a type id is `type.<name>`")
            elif kind == "tag" and (segs[0] != "tag" or len(segs) < 2):
                self.errors.append(f"{tid}: a tag id is `tag.<path>`")
            elif kind == "relation" and (segs[0] != "rel" or len(segs) != 2):
                self.errors.append(f"{tid}: a relation id is `rel.<name>`")
            elif kind == "vocab" and (len(segs) != 3 or segs[0] not in types):
                self.errors.append(f"{tid}: a vocabulary id is `<declared type>.<field>.<value>`")
            elif kind == "entity" and (len(segs) != 2 or segs[0] in ("type", "tag", "rel")):
                self.errors.append(f"{tid}: an entity id is `<namespace>.<slug>`")
            st = t.get("status")
            if st not in STATUSES:
                self.errors.append(f"{tid}: status must be one of {'|'.join(STATUSES)} (got {st!r})")
            rb = t.get("replaced-by")
            if rb and rb not in self.terms:
                self.errors.append(f"{tid}: replaced-by `{rb}` is not a declared term")
        for bkey, spec in self.fields.items():
            kind = spec.get("kind")
            if kind not in ("type", "vocab", "entity", "tag", "relation"):
                self.errors.append(f"fields.{bkey}: kind must be type|vocab|entity|tag|relation")
            if kind == "relation":
                rel = spec.get("relation")
                if not rel or rel not in self.terms or self.terms[rel]["_kind"] != "relation":
                    self.errors.append(f"fields.{bkey}: relation `{rel}` is not declared under relations:")
        seen: dict = {}
        for t in self.terms.values():
            if t["_kind"] == "relation":
                continue
            parent = None if t["_kind"] == "tag" else term_parent(t)
            k = (t["_kind"], parent, term_value(t))
            if k in seen:
                self.errors.append(f"{t['_id']}: value `{term_value(t)}` already belongs to {seen[k]}")
            seen[k] = t["_id"]


def load_ontology_file(path: Path) -> Ontology:
    try:
        return Ontology(parse_onto_yaml(path.read_text(encoding="utf-8")))
    except OntologyError as e:
        raise OntologyError(f"{path.name}: {e}")


# ----------------------------------------------------------------------------- project

class Project:
    def __init__(self, root: Path, config: dict, onto: Ontology | None, onto_error: str | None = None):
        self.root = root
        self.config = config
        self.onto = onto
        self.onto_error = onto_error

    @classmethod
    def load(cls, root: Path, require: bool = True) -> "Project | None":
        cfg_path = root / CONFIG_REL
        if not cfg_path.exists():
            if require:
                die(f"no project-ontology config at {cfg_path} — run /ontology:init first")
            return None
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        path = root / cfg["ontology_file"]
        if not path.exists():
            return cls(root, cfg, None, f"ontology file missing: {cfg['ontology_file']}")
        try:
            return cls(root, cfg, load_ontology_file(path))
        except OntologyError as e:
            return cls(root, cfg, None, str(e))

    @property
    def ontology_path(self) -> Path:
        return self.root / self.config["ontology_file"]

    def roots(self) -> list[str]:
        return [str(r).strip("/") for r in self.config.get("roots", [])]

    def split_governed(self, rel: str) -> tuple[str, str] | None:
        """project-relative path → (root, path inside root) when the file is governed markdown."""
        if not rel or not rel.lower().endswith(".md"):
            return None
        for r in self.roots():
            prefix = "" if r in ("", ".") else r + "/"
            if prefix and not rel.startswith(prefix):
                continue
            inner = rel[len(prefix):]
            if any(part.startswith(".") for part in Path(inner).parts):
                continue
            if any(fnmatch.fnmatch(inner, ex) for ex in self.config.get("exclude", [])):
                continue
            return r, inner
        return None

    def iter_governed(self):
        for r in self.roots():
            base = self.root / r
            if not base.is_dir():
                continue
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
                for fn in sorted(filenames):
                    rel = rel_posix(Path(dirpath) / fn, self.root)
                    if rel and self.split_governed(rel):
                        yield rel

    def derive_id(self, rel: str, ptype: str | None) -> str:
        sp = self.split_governed(rel)
        inner = sp[1] if sp else rel
        parts = Path(inner).parts
        folders = self.onto.scope_folders if self.onto and self.onto.scope_folders else DEFAULT_SCOPE_FOLDERS
        notes = self.onto.folder_notes if self.onto else DEFAULT_FOLDER_NOTES
        prefix, rest = [], list(parts)
        if len(parts) >= 3 and parts[0] in folders:
            prefix, rest = [folders[parts[0]], slugify(parts[1])], list(parts[2:])
        stem = Path(parts[-1]).stem
        if prefix and len(rest) == 1 and stem.lower() in notes:
            return ".".join(prefix)
        seg = slugify(stem) or "page"
        return ".".join(prefix + [slugify(ptype) if ptype else "page", seg])


class FileIndex:
    """Every file under the governed roots (not only governed pages — links may point at excluded
    pages such as _schema/SCHEMA.md, or at attachments). Types and titles are read lazily."""

    def __init__(self, proj: Project, overrides: dict[str, str | None] | None = None, suggest: bool = True):
        self.proj = proj
        self.overrides = overrides or {}  # rel → text (None = deleted) for a write being simulated
        self.suggest = suggest            # nearest-page suggestions: per-file checks yes, vault-wide sweeps no
        self.by_stem: dict[str, list[str]] = {}
        self.by_name: dict[str, list[str]] = {}
        self.by_folder: dict[str, list[str]] = {}
        self.inner: dict[str, str] = {}
        self._nearest: dict[str, list[str]] = {}
        self._types: dict[str, str | None] = {}
        self._titles: dict[str, list[str]] | None = None
        files = []
        for r in proj.roots():
            base = proj.root / r
            if not base.is_dir():
                continue
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                for fn in filenames:
                    if fn.startswith("."):
                        continue
                    rel = rel_posix(Path(dirpath) / fn, proj.root)
                    if rel:
                        files.append((rel, r))
        for rel, text in self.overrides.items():
            if text is not None and not any(rel == f for f, _ in files):
                for r in proj.roots():
                    prefix = "" if r in ("", ".") else r + "/"
                    if not prefix or rel.startswith(prefix):
                        files.append((rel, r))
                        break
        for rel, text in self.overrides.items():
            if text is None:
                files = [(f, r) for f, r in files if f != rel]
        link_exclude = proj.config.get("link_exclude", DEFAULT_LINK_EXCLUDE)
        for rel, r in sorted(set(files)):
            prefix = "" if r in ("", ".") else r + "/"
            inner = rel[len(prefix):]
            if any(fnmatch.fnmatch(inner, ex) for ex in link_exclude):
                continue  # page templates are scaffolds, not link targets ([[gap|x]] would "resolve" to templates/gap.md)
            self.inner[rel] = inner
            parts = inner.split("/")
            name = parts[-1]
            if name.lower().endswith(".md"):
                stem = name[:-3].lower()
                self.by_stem.setdefault(stem, []).append(rel)
                if len(parts) >= 2 and stem in (proj.onto.folder_notes if proj.onto else DEFAULT_FOLDER_NOTES):
                    self.by_folder.setdefault(parts[-2].lower(), []).append(rel)
            self.by_name.setdefault(name.lower(), []).append(rel)

    def text(self, rel: str) -> str:
        if rel in self.overrides:
            return self.overrides[rel] or ""
        try:
            return (self.proj.root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def page_type(self, rel: str) -> str | None:
        if rel not in self._types:
            data, _, _ = frontmatter_items(self.text(rel))
            t = (data or {}).get("type")
            self._types[rel] = t.strip().lower() if isinstance(t, str) and t.strip() and "|" not in t else None
        return self._types[rel]

    def titles(self) -> dict[str, list[str]]:
        if self._titles is None:
            self._titles = {}
            for stem_list in self.by_stem.values():
                for rel in stem_list:
                    self._titles.setdefault(page_title(self.text(rel), Path(rel).stem).strip().lower(), []).append(rel)
        return self._titles

    def canonical_target(self, rel: str) -> str:
        """Link text that resolves to exactly this file in every resolver (Obsidian, project-db, this
        engine): the stem when it is unique, else the full path inside the vault without `.md`."""
        inner = self.inner.get(rel, rel)
        noext = inner[:-3] if inner.lower().endswith(".md") else inner
        stem = Path(noext).name
        return stem if len(self.by_stem.get(stem.lower(), [])) <= 1 else noext

    def resolve(self, target: str, label: str | None, type_words: set[str]) -> tuple[str, list[str], str | None]:
        """→ (status, candidates, how). status: ok | ambiguous | noncanonical | broken."""
        t = target.strip().replace("\\", "/").strip("/")
        if t.lower().endswith(".md"):
            t = t[:-3]
        key = t.lower()
        if not key:
            return "broken", [], None
        ext = re.search(r"\.([A-Za-z0-9]{1,5})$", key)
        if ext:  # attachment or explicit extension
            c = [r for r in self.by_name.get(key.split("/")[-1], []) if "/" not in key or r.lower().endswith(key)]
            if len(c) == 1:
                return "ok", c, "exact"
            if len(c) > 1:
                return "ambiguous", c, "exact"
        if "/" in key:
            stem = key.split("/")[-1]
            c = [r for r in self.by_stem.get(stem, []) if (self.inner[r][:-3].lower() == key or self.inner[r][:-3].lower().endswith("/" + key))]
        else:
            c = list(self.by_stem.get(key, []))
        if len(c) == 1:
            return "ok", c, "exact"
        if len(c) > 1:
            return "ambiguous", c, "exact"
        def by_label():
            if not label or not (key in type_words or key.rstrip("s") in type_words):
                return []
            lk = label.strip().lower()
            c2 = self.by_stem.get(lk) or self.by_stem.get(slugify(lk)) or self.titles().get(lk, [])
            typed = [r for r in c2 if self.page_type(r) in (key, key.rstrip("s"))]
            return typed if len(c2) > 1 and len(typed) == 1 else c2

        for how, cands in (("title", lambda: self.titles().get(key, [])),
                           ("slug", lambda: self.by_stem.get(slugify(key), [])),
                           ("label", by_label),
                           ("folder", lambda: self.by_folder.get(key, []))):
            c = list(dict.fromkeys(cands()))
            if len(c) == 1:
                return "noncanonical", c, how
            if len(c) > 1:
                return "ambiguous", c, how
        return "broken", [], None

    def nearest_pages(self, target: str, n: int = 3) -> list[str]:
        if not self.suggest:
            return []
        key = slugify(target) or target.lower()
        if key not in self._nearest:
            self._nearest[key] = difflib.get_close_matches(key, list(self.by_stem.keys()), n=n, cutoff=0.6)
        return self._nearest[key]


# ----------------------------------------------------------------------------- rules

def _ratchet_key(v: dict) -> tuple:
    return (v["rule"], v.get("field") or "", str(v.get("value") or "").strip().lower())


def _nearest_terms(value: str, terms: list[dict], n: int = 3) -> list[str]:
    scored = []
    for i, t in enumerate(terms):
        names = [term_value(t)] + [str(a) for a in as_list(t.get("aliases"))] + ([str(t["label"])] if t.get("label") else [])
        s = max(difflib.SequenceMatcher(None, value.lower(), x.lower()).ratio() for x in names)
        if any(x.lower().startswith(value.lower()) or value.lower().startswith(x.lower()) for x in names if len(x) >= 2 and len(value) >= 2):
            s = max(s, 0.75)
        scored.append((s, i, term_value(t)))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [v for s, _, v in scored if s >= 0.6][:n]


def _propose_hint(kind: str, parent: str | None, value: str) -> str:
    leaf = EMOJI_LEAVES.get(value) or slugify(value) or "term"
    if kind == "tag":
        tid = "tag." + ".".join(slugify(p) or "x" for p in value.split("/"))
    elif kind == "type":
        tid = f"type.{leaf}"
    else:
        tid = f"{parent}.{leaf}"
    extra = "" if leaf == value else f" --value {shlex.quote(value)}"
    return f"{ENGINE_CMD} propose {tid}{extra} --label {shlex.quote(value)} --definition \"<what it means>\""


def value_violations(onto: Ontology, bkey: str, spec: dict, ptype: str | None, item: dict, value: str) -> list[dict]:
    kind, parent = onto.domain_parent(bkey, spec, ptype)
    family = "type" if kind == "type" else kind
    namespace = (ptype if kind == "vocab" else parent if kind == "entity" else kind)
    field = item["key"]
    base = {"family": family, "binding": bkey, "field": field, "value": value, "line": item.get("line"),
            "start": item.get("start"), "end": item.get("end")}
    what = {"vocab": f"{parent} value", "entity": f"{parent} entity", "tag": "tag", "type": "page type"}.get(kind, kind)
    term, how = onto.match(kind, parent, value)
    dom = onto.domain(kind, parent)
    approved = [t for t in dom["terms"] if t.get("status") == "approved"]
    out = []

    def add(rule, message, **kw):
        v = dict(base, rule=rule, message=message, **kw)
        v["policy"] = onto.policy_for(rule, family, bkey, namespace)
        if rule == "value-proposed" and v["policy"] == "strict":
            v["suggestion"] = "blocked until a human approves it (/ontology:approve) — policy.proposed is strict"
        if v["policy"] != "off":
            out.append(v)

    if term is None:
        near = _nearest_terms(value, approved)
        allowed = [term_value(t) for t in approved]
        listing = (" · ".join(allowed) if len(allowed) <= 24 else " · ".join(allowed[:24]) + f" · … (+{len(allowed) - 24})") or "(none approved yet)"
        rule = "type-unknown" if kind == "type" else "value-unknown"
        msg = f"{field}: `{value}` is not a registered {what}"
        add(rule, msg, nearest=near, allowed=allowed[:40],
            suggestion=(f"closest: {' · '.join(near)} — " if near else "") + f"approved: {listing}",
            fix=_propose_hint(kind, parent, value))
        return out
    tid = term["_id"]
    if term.get("status") == "deprecated":
        rb = term.get("replaced-by")
        repl = term_value(onto.terms[rb]) if rb in onto.terms else None
        add("type-deprecated" if kind == "type" else "value-deprecated",
            f"{field}: `{value}` is deprecated ({tid})" + (f" — replaced by `{repl}` ({rb})" if repl else "")
            + (f": {term['reason']}" if term.get("reason") else ""),
            term=tid, replacement=repl, suggestion=(f"use `{repl}`" if repl else "choose an approved value"),
            fix=(f"{ENGINE_CMD} apply {{path}}" if repl else ""))
        return out
    if how in ("alias", "variant", "proposed-alias"):
        canon = term_value(term)
        note = {"alias": "an alias", "variant": "a spelling variant", "proposed-alias": "an alias awaiting approval"}[how]
        add("value-noncanonical", f"{field}: `{value}` is {note} of `{canon}` ({tid})", term=tid, replacement=canon,
            suggestion=f"write `{canon}`", fix=f"{ENGINE_CMD} apply {{path}}")
    if term.get("status") == "proposed":
        add("value-proposed", f"{field}: `{term_value(term)}` ({tid}) is proposed, not yet approved", term=tid,
            suggestion="usable now; a human approves it with /ontology:approve", fix="")
    return out


def _link_violation(onto, index, rule_prefix, family, field, bkey, namespace, raw, target, label, line, start, end,
                    range_types=None, relation_id=None) -> list[dict]:
    status, cands, how = index.resolve(target, label, onto.type_values())
    out = []
    base = {"family": family, "binding": bkey, "field": field, "value": raw, "target": target, "line": line, "start": start, "end": end}

    def add(rule, message, **kw):
        v = dict(base, rule=f"{rule_prefix}-{rule}", message=message, **kw)
        v["policy"] = onto.policy_for(v["rule"], family, bkey, namespace)
        if v["policy"] != "off":
            out.append(v)

    if status == "broken":
        near = index.nearest_pages(target)
        add("broken", f"{raw} resolves to no page", nearest=near,
            suggestion=("closest pages: " + " · ".join(f"[[{n}]]" for n in near)) if near else "create the page or fix the target",
            fix="")
        return out
    if status == "ambiguous":
        forms = [f"[[{index.canonical_target(c)}" + (f"|{label}" if label else "") + "]]" for c in cands[:4]]
        add("ambiguous", f"{raw} matches {len(cands)} pages", candidates=cands[:6],
            suggestion="qualify the target: " + " · ".join(forms), fix="")
        return out
    target_rel = cands[0]
    canon = index.canonical_target(target_rel)
    if status == "noncanonical":
        display = (label or target).strip()
        repl = f"[[{canon}|{display}]]" if ("/" in canon or display.lower() != canon.lower()) else f"[[{canon}]]"
        add("noncanonical", f"{raw} only resolves by {how} to {target_rel}", replacement=repl, resolved=target_rel,
            suggestion=f"write {repl}", fix=f"{ENGINE_CMD} apply {{path}}")
    if range_types:
        ttype = index.page_type(target_rel)
        if ttype not in range_types:
            add("range", f"{field}: {raw} points at a `{ttype or 'untyped'}` page; {relation_id} expects {'|'.join(range_types)}",
                resolved=target_rel, suggestion=f"link a {'|'.join(range_types)} page", fix="")
    return out


def _quote_offset(raw: str) -> int:
    return 1 if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'" else 0


def check_text(proj: Project, rel: str, text: str, index: FileIndex) -> list[dict]:
    """The rule set. Every caller — hooks, check, project-db, wiki-lint — goes through here."""
    onto = proj.onto
    data, items, body_at = frontmatter_items(text)
    viols: list[dict] = []
    by_key: dict[str, list[dict]] = OrderedDict()
    for it in items:
        by_key.setdefault(it["key"], []).append(it)
    raw_type = (data or {}).get("type")
    ptype = raw_type.strip().lower() if isinstance(raw_type, str) and raw_type.strip() and "|" not in raw_type else None
    ignored = ptype in onto.ignore_types if ptype else False
    type_words = onto.type_values()
    for key, its in by_key.items():
        b = onto.binding(ptype, key)
        if b and (key == "type" or not ignored):
            bkey, spec = b
            kind = spec.get("kind")
            if kind == "relation":
                rel_term = onto.terms.get(spec.get("relation") or "", {})
                rng = [str(x).lower() for x in as_list(rel_term.get("range"))]
                for it in its:
                    sval = _unquote(it["raw"])
                    links = list(WIKILINK_RE.finditer(sval))
                    if not links:
                        v = {"family": "relation", "binding": bkey, "field": key, "value": sval, "line": it["line"],
                             "rule": "relation-broken", "message": f"{key}: `{sval}` is not a [[wikilink]] ({spec.get('relation')})",
                             "suggestion": "write the target as \"[[page]]\"", "fix": ""}
                        v["policy"] = onto.policy_for("relation-broken", "relation", bkey, spec.get("relation"))
                        if v["policy"] != "off":
                            viols.append(v)
                        continue
                    for lm in links:
                        at = it["start"] + _quote_offset(it["raw"]) + lm.start()
                        viols += _link_violation(onto, index, "relation", "relation", key, bkey, spec.get("relation"), lm.group(0),
                                                 lm.group(1), lm.group(2), it["line"], at, at + len(lm.group(0)), rng, spec.get("relation"))
                continue
            if kind in ("vocab", "entity", "tag", "type"):
                for it in its:
                    sval = _unquote(it["raw"])
                    if sval == "":
                        continue
                    parts = [(sval, 0, len(sval))]
                    if kind == "tag" and "," in sval and not it["raw"].startswith(("'", '"')):
                        parts = [(p, s, e) for s, e, p in split_comma_tokens(sval)]
                    if kind == "vocab" and bkey.startswith("*.") and not ptype:
                        continue  # a per-type vocabulary cannot apply to a page without a type
                    for pval, s, e in parts:
                        sub = dict(it, start=it["start"] + s, end=it["start"] + e) if len(parts) > 1 else it
                        if kind == "type" and pval != sval:
                            continue
                        viols += value_violations(onto, bkey, spec, ptype, sub, pval)
                continue
        # unbound (or ignored-type) frontmatter strings: links inside them are still links
        for it in its:
            sval = _unquote(it["raw"])
            for lm in WIKILINK_RE.finditer(sval):
                at = it["start"] + _quote_offset(it["raw"]) + lm.start()
                viols += _link_violation(onto, index, "link", "link", key, None, None, lm.group(0), lm.group(1), lm.group(2),
                                         it["line"], at, at + len(lm.group(0)))
    body = text[body_at:]
    first_line = text[:body_at].count("\n")
    shown = visible_body(body)  # same length as body: offsets in `shown` are offsets in the file
    offset = body_at
    for n, line in enumerate(shown.split("\n")):
        for lm in WIKILINK_RE.finditer(line):
            at = offset + lm.start()
            viols += _link_violation(onto, index, "link", "link", None, None, None, lm.group(0), lm.group(1), lm.group(2),
                                     first_line + n + 1, at, at + len(lm.group(0)))
        offset += len(line) + 1
    for v in viols:
        v["path"] = rel
    return viols


def check_all(proj: Project, index: FileIndex | None = None) -> tuple[list[dict], dict[str, dict]]:
    """Every governed page. Returns (violations, pages{rel: {id, type}}) and adds id-duplicate."""
    index = index or FileIndex(proj, suggest=False)
    viols, pages, ids = [], {}, {}
    for rel in proj.iter_governed():
        text = index.text(rel)
        viols += check_text(proj, rel, text, index)
        ptype = index.page_type(rel)
        pid = proj.derive_id(rel, ptype)
        pages[rel] = {"id": pid, "type": ptype}
        ids.setdefault(pid, []).append(rel)
    for pid, rels in ids.items():
        if len(rels) > 1:
            for rel in rels:
                pol = proj.onto.policy_for("id-duplicate", "id", None, None)
                if pol != "off":
                    viols.append({"path": rel, "family": "id", "rule": "id-duplicate", "field": None, "value": pid, "line": None,
                                  "policy": pol, "message": f"derived id `{pid}` is shared by {len(rels)} pages: {', '.join(rels)}",
                                  "suggestion": "rename one of the files", "fix": ""})
    return viols, pages


def summarize(viols: list[dict]) -> dict:
    return {"violations": len(viols), "strict": sum(1 for v in viols if v["policy"] == "strict"),
            "warn": sum(1 for v in viols if v["policy"] == "warn"), "pages": len({v["path"] for v in viols}),
            "by_rule": dict(sorted(Counter(v["rule"] for v in viols).items()))}


def term_counts(onto: Ontology) -> dict:
    c = Counter(t.get("status") for t in onto.terms.values())
    by_kind = {}
    for t in onto.terms.values():
        by_kind.setdefault(t["_kind"], Counter())[t.get("status")] += 1
    return {"terms": len(onto.terms), "approved": c.get("approved", 0), "proposed": c.get("proposed", 0),
            "deprecated": c.get("deprecated", 0), "by_kind": {k: dict(v) for k, v in by_kind.items()}}


# ----------------------------------------------------------------------------- output

def format_violations(viols: list[dict], fmt: str = "text", show_fix: bool = True) -> str:
    if fmt == "json":
        keep = ("path", "line", "rule", "policy", "family", "field", "value", "message", "suggestion", "fix", "nearest", "replacement", "term", "binding")
        return json.dumps([{k: v.get(k) for k in keep if v.get(k) not in (None, [], "")} for v in viols], ensure_ascii=False, indent=1)
    if fmt == "lint":
        out = []
        for v in viols:
            sev = "HIGH" if v["policy"] == "strict" else "LOW"
            if v["rule"] == "link-broken" and v["policy"] == "strict":
                sev = "CRITICAL"
            out.append(f"ONTOLOGY_VIOLATION | {sev} |\n  Page: {v['path']}" + (f":{v['line']}" if v.get("line") else "")
                       + f"\n  Rule: {v['rule']} ({v['policy']})\n  Issue: {v['message']}\n  Recommendation: {v.get('suggestion') or '—'}"
                       + (f"\n  Fix: {v['fix'].replace('{path}', v['path'])}" if v.get("fix") else ""))
        return "\n\n".join(out)
    out, cur = [], None
    for v in sorted(viols, key=lambda x: (x["path"], x.get("line") or 0, x["rule"])):
        if v["path"] != cur:
            cur = v["path"]
            out.append(cur)
        mark = "✗" if v["policy"] == "strict" else "!"
        out.append(f"  {mark} L{v.get('line') or '-'} {v['rule']} [{v['policy']}] {v['message']}")
        if v.get("suggestion"):
            out.append(f"      {v['suggestion']}")
        if show_fix and v.get("fix"):
            out.append(f"      fix: {v['fix'].replace('{path}', v['path'])}")
    return "\n".join(out)


# ----------------------------------------------------------------------------- write simulation (hooks)

def simulate_write(tool: str, ti: dict, old: str | None) -> str | None:
    """The text a Write / Edit / MultiEdit call would leave on disk, or None when the tool itself would
    fail (the hook then stays out of the way and lets the tool report its own error)."""
    if tool == "Write":
        new = ti.get("content", ti.get("contents"))
        return new if isinstance(new, str) else None
    edits = []
    if tool == "Edit":
        edits = [ti]
    elif tool == "MultiEdit":
        edits = ti.get("edits") or []
    else:
        return None
    text = old
    for e in edits:
        o, n = e.get("old_string"), e.get("new_string")
        if not isinstance(o, str) or not isinstance(n, str):
            return None
        if text is None:
            if o == "":
                text = n
                continue
            return None
        if o == "":
            return None
        count = text.count(o)
        if count == 0 or (count > 1 and not e.get("replace_all")):
            return None
        text = text.replace(o, n) if e.get("replace_all") else text.replace(o, n, 1)
    return text


def _hook_path(data: dict, root: Path) -> Path | None:
    ti = data.get("tool_input") or {}
    p = ti.get("file_path") or ti.get("path") or ti.get("notebook_path")
    if not p:
        return None
    path = Path(p)
    if not path.is_absolute():
        path = Path(data.get("cwd") or root) / path
    return path


def _onto_status_changes(old: Ontology | None, new: Ontology) -> list[str]:
    """Human-gate transitions an agent may not make by editing the file directly: approving or deprecating
    a term, adding approved aliases, removing or re-spelling a term that is not merely proposed, and
    loosening policy (including switching `approval` away from human)."""
    out = []
    if old is not None:
        for key, before, after in (("policy.default", old.policy_default, new.policy_default), ("policy.proposed", old.policy_proposed, new.policy_proposed),
                                   ("policy.approval", old.approval, new.approval)):
            if before != after:
                out.append(f"{key}: {before} → {after}")
        if old.overrides != new.overrides:
            out.append(f"policy.overrides: {old.overrides} → {new.overrides}")
        for tid, t in old.terms.items():
            if t.get("status") == "proposed":
                continue
            if tid not in new.terms:
                out.append(f"{tid}: {t.get('status')} term removed")
            elif term_value(t) != term_value(new.terms[tid]):
                out.append(f"{tid}: value `{term_value(t)}` → `{term_value(new.terms[tid])}`")
        for bkey in old.fields:
            if bkey not in new.fields:
                out.append(f"fields.{bkey}: controlled field removed")
    for tid, t in new.terms.items():
        before = old.terms.get(tid) if old else None
        was = before.get("status") if before else None
        if t.get("status") == "approved" and was != "approved":
            out.append(f"{tid}: {was or 'new'} → approved")
        if t.get("status") == "deprecated" and was != "deprecated":
            out.append(f"{tid}: {was or 'new'} → deprecated")
        if before is not None:
            added = set(map(str, as_list(t.get("aliases")))) - set(map(str, as_list(before.get("aliases"))))
            if added:
                out.append(f"{tid}: approved aliases added {sorted(added)}")
        elif as_list(t.get("aliases")):
            out.append(f"{tid}: new term with approved aliases")
    return out


def hook_pre(data: dict, root: Path) -> tuple[int, str]:
    tool = data.get("tool_name") or ""
    proj = Project.load(root, require=False)
    if proj is None:
        return 0, ""
    path = _hook_path(data, root)
    if path is None:
        return 0, ""
    rel = rel_posix(path, root)
    if rel is None:
        return 0, ""
    ti = data.get("tool_input") or {}
    try:
        old = path.read_text(encoding="utf-8", errors="replace") if path.exists() else None
    except OSError:
        old = None
    # the ontology file itself: must parse, must validate no worse than before, and agents may not approve
    if rel == proj.config["ontology_file"]:
        new = simulate_write(tool, ti, old)
        if new is None or new == old:
            return 0, ""
        try:
            new_onto = Ontology(parse_onto_yaml(new))
        except OntologyError as e:
            return 2, f"project-ontology blocked this write: {rel} would not parse — {e}"
        old_onto = None
        if old is not None:
            try:
                old_onto = Ontology(parse_onto_yaml(old))
            except OntologyError:
                old_onto = None
        added_errors = [e for e in new_onto.errors if not old_onto or e not in old_onto.errors]
        msgs = []
        if added_errors:
            msgs.append("invalid terms:\n" + "\n".join(f"  ✗ {e}" for e in added_errors[:12]))
        if (old_onto.approval if old_onto else new_onto.approval) == "human":
            gate = _onto_status_changes(old_onto, new_onto)
            if gate:
                msgs.append("approving, deprecating, removing terms and changing policy are a human gate (policy.approval: human) — "
                            "an agent may add or edit *proposed* terms only:\n" + "\n".join(f"  ✗ {g}" for g in gate[:12])
                            + f"\n  ask the user, then run `{ENGINE_CMD} approve <id> --by <their name>` / `deprecate …` (or /ontology:approve)")
        if msgs:
            return 2, f"project-ontology blocked this write to {rel}:\n" + "\n".join(msgs)
        return 0, ""
    if not proj.split_governed(rel):
        return 0, ""
    if proj.onto is None:
        return 2, (f"project-ontology blocked this write: the ontology cannot be loaded ({proj.onto_error}). "
                   f"Fix {proj.config['ontology_file']} first — pages cannot be checked against a broken ontology.")
    new = simulate_write(tool, ti, old)
    if new is None or new == old:
        return 0, ""
    index = FileIndex(proj, overrides={rel: new})
    before = check_text(proj, rel, old, index) if old is not None else []
    after = check_text(proj, rel, new, index)
    had = Counter(_ratchet_key(v) for v in before)
    fresh = []
    for v in after:
        k = _ratchet_key(v)
        if had[k] > 0:
            had[k] -= 1
        elif v["policy"] == "strict":
            fresh.append(v)
    if not fresh:
        return 0, ""
    lines = [f"project-ontology blocked this write: {rel} — {len(fresh)} new strict violation(s)"]
    for v in fresh[:10]:
        lines.append(f"  ✗ L{v.get('line') or '-'} {v['rule']} · {v['message']}")
        if v.get("suggestion"):
            lines.append(f"      {v['suggestion']}")
        if v.get("rule") in ("value-unknown", "type-unknown") and v.get("fix"):
            if proj.onto.policy_proposed == "strict":
                lines.append("      if this is a genuinely new concept, propose it — with policy.proposed: strict it stays blocked")
                lines.append("      until a human approves it:")
            else:
                lines.append("      if this is a genuinely new concept, register it first (proposed terms are usable at once;")
                lines.append("      a human approves them later):")
            lines.append(f"      {v['fix']}")
        elif v.get("fix"):
            lines.append(f"      fix: {v['fix'].replace('{path}', rel)}")
    if len(fresh) > 10:
        lines.append(f"  … {len(fresh) - 10} more")
    remaining = len(after) - len(fresh)
    if remaining:
        lines.append(f"  ({remaining} pre-existing or non-blocking violation(s) in this file are not blocking — `{ENGINE_CMD} check {rel}`)")
    lines.append(f"  Rules: {proj.config.get('doc_file') or proj.config['ontology_file']}. Fix the values; do not route around this hook with Bash writes.")
    return 2, "\n".join(lines)


def hook_post(data: dict, root: Path) -> tuple[int, str]:
    proj = Project.load(root, require=False)
    if proj is None:
        return 0, ""
    path = _hook_path(data, root)
    rel = rel_posix(path, root) if path else None
    if rel is None or not path.exists():
        return 0, ""
    if rel == proj.config["ontology_file"]:
        if proj.onto is not None:
            render_all(proj, templates=False)
            return 0, json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                  "additionalContext": f"project-ontology: {proj.config.get('doc_file')} re-rendered from {rel}."}})
        return 0, ""
    if not proj.split_governed(rel) or proj.onto is None:
        return 0, ""
    index = FileIndex(proj)
    viols = check_text(proj, rel, path.read_text(encoding="utf-8", errors="replace"), index)
    if not viols:
        return 0, ""
    s = summarize(viols)
    body = [f"project-ontology: {rel} still has {s['violations']} violation(s) (strict {s['strict']} pre-existing · warn {s['warn']}) — not blocking:"]
    for v in viols[:8]:
        body.append(f"- L{v.get('line') or '-'} {v['rule']} [{v['policy']}]: {v['message']}" + (f" — {v['suggestion']}" if v.get("suggestion") else ""))
    if len(viols) > 8:
        body.append(f"- … {len(viols) - 8} more: {ENGINE_CMD} check {rel}")
    return 0, json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "\n".join(body)}}, ensure_ascii=False)


_GOV_CMD_RE = re.compile(r"ontology\.py\b[^\n;&|]*(\b(approve|deprecate)\b|\binit\b[^\n;&|]*--write)")


def _bash_write_targets(command: str) -> list[str]:
    """Paths a shell command would write: redirections, tee, sed/perl in-place, cp/mv destinations."""
    targets = []
    for m in re.finditer(r"(?:^|[^0-9&<>])>{1,2}\s*([\"']?)([^\s;&|\"'<>]+)\1", command):
        targets.append(m.group(2))
    try:
        segments = re.split(r"(?:&&|\|\||;|\||\n)", command)
        for seg in segments:
            try:
                toks = shlex.split(seg, posix=True)
            except ValueError:
                toks = seg.split()
            if not toks:
                continue
            prog = Path(toks[0]).name
            args = toks[1:]
            if prog == "tee":
                targets += [t for t in args if not t.startswith("-")]
            elif prog in ("sed", "gsed", "perl") and any(re.match(r"^-[A-Za-z]*i", t) for t in args):
                targets += [t for t in args if t.lower().endswith(".md")]
            elif prog in ("cp", "mv", "install", "rsync") and len([t for t in args if not t.startswith("-")]) >= 2:
                targets.append([t for t in args if not t.startswith("-")][-1])
    except Exception:
        pass
    return targets


def hook_bash(data: dict, root: Path) -> tuple[int, str]:
    proj = Project.load(root, require=False)
    if proj is None:
        return 0, ""
    cmd = str((data.get("tool_input") or {}).get("command") or "")
    approval = proj.onto.approval if proj.onto else "human"
    if _GOV_CMD_RE.search(cmd) and approval == "human":
        return 0, json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                              "permissionDecisionReason": "project-ontology: approving, deprecating or declaring terms (init --write) is a human gate — confirm this change yourself."}})
    cwd = Path(data.get("cwd") or root)
    blocked = []
    for t in _bash_write_targets(cmd):
        p = Path(t)
        p = p if p.is_absolute() else cwd / p
        rel = rel_posix(p, root)
        if rel and (proj.split_governed(rel) or rel == proj.config["ontology_file"]):
            blocked.append(rel)
    if blocked:
        return 2, ("project-ontology blocked this Bash command: it writes governed pages outside the ontology hook ("
                   + ", ".join(sorted(set(blocked))[:5]) + "). Use the Write/Edit tools so the ontology check runs, "
                   f"or `{ENGINE_CMD} apply` for mechanical rewrites.")
    return 0, ""


# ----------------------------------------------------------------------------- init: mining

def detect_wiki(root: Path) -> str | None:
    for cand in ("wiki", ".claude/wiki", "docs/wiki"):
        w = root / cand
        if (w / "_schema" / "SCHEMA.md").exists() or (w / "_index.md").exists():
            return cand
    return None


_VOCAB_TOKEN = r"[^\s|#,]+"
_TEMPLATE_VOCAB_RE = re.compile(rf"^(?:(?P<binding>[a-z0-9*][a-z0-9.*_-]*)\s*:\s*)?(?P<vals>{_VOCAB_TOKEN}(?:\|{_VOCAB_TOKEN})+)\s*$")


def parse_template_vocab(comment: str) -> list[str] | None:
    m = _TEMPLATE_VOCAB_RE.match(comment.strip())
    return [v.strip() for v in m.group("vals").split("|")] if m else None


def mine_templates(tdir: Path) -> dict:
    out: dict = {}
    if not tdir.is_dir():
        return out
    for p in sorted(tdir.glob("*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        fm, _ = split_frontmatter(text)
        if fm is None:
            continue
        data, docs = parse_frontmatter(fm)
        t = data.get("type")
        t = str(t).strip().lower() if isinstance(t, str) and t.strip() and "|" not in t else p.stem.lower()
        entry = out.setdefault(t, {"file": p.name, "keys": [], "vocab": {}})
        for k in data.keys():
            entry["keys"].append(k)
            vals = parse_template_vocab(docs.get(k) or "")
            if vals:
                entry["vocab"][k] = vals
    return out


def mine_schema(schema: Path) -> dict:
    """Vocabularies declared in SCHEMA.md fenced YAML blocks: {type or '*': {field: {values, line}}},
    plus type definitions (`**Definition**:` under a heading naming the type) and declared types."""
    out: dict = {"vocab": {}, "definitions": {}, "types": []}
    if not schema.exists():
        return out
    text = schema.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if re.match(r"^\s*```ya?ml\s*$", lines[i]):
            j = i + 1
            block = []
            while j < len(lines) and not re.match(r"^\s*```\s*$", lines[j]):
                block.append((j + 1, lines[j]))
                j += 1
            btype = "*"
            for _, ln in block:
                m = re.match(r"^type:\s*([A-Za-z0-9_\-|]+)\s*(?:#.*)?$", ln.strip())
                if m:
                    if "|" in m.group(1):
                        for t in m.group(1).split("|"):
                            if t and t not in out["types"]:
                                out["types"].append(t)
                    else:
                        btype = m.group(1).lower()
                    break
            for lineno, ln in block:
                m = re.match(r"^([A-Za-z0-9_\-]+):\s*(.+?)\s*$", ln)
                if not m or m.group(1) == "type":
                    continue
                val, _ = _strip_comment(" " + m.group(2))
                val = val.strip()
                if "|" not in val or " " in val or val.startswith("[") or ":" in val:
                    continue
                vals = [v for v in val.split("|") if v and not v.startswith("{")]
                if vals:
                    out["vocab"].setdefault(btype, {}).setdefault(m.group(1), {"values": vals, "line": lineno})
            i = j + 1
            continue
        i += 1
    for n, ln in enumerate(lines):
        hm = re.match(r"^#{2,4}\s+(?:\d+(?:\.\d+)*\s+)?([A-Za-z][A-Za-z \-]*)\s*$", ln)
        if hm:
            name = hm.group(1).strip().lower()
            for k in range(n + 1, min(n + 6, len(lines))):
                dm = re.match(r"^\*\*Definition\*\*:\s*(.+)$", lines[k].strip())
                if dm:
                    out["definitions"].setdefault(name, dm.group(1).strip())
                    break
    return out


def scan_project(proj: Project) -> dict:
    cfg, root = proj.config, proj.root
    tmpl = mine_templates(root / cfg["templates_dir"]) if cfg.get("templates_dir") else {}
    schema = mine_schema(root / cfg["schema_file"]) if cfg.get("schema_file") else {"vocab": {}, "definitions": {}, "types": []}
    stub = Ontology({"ids": {"scope-folders": {}}})
    proj.onto = proj.onto or stub
    pages = []
    index = FileIndex(proj, suggest=False)
    for rel in proj.iter_governed():
        text = index.text(rel)
        data, items, _ = frontmatter_items(text)
        raw = (data or {}).get("type")
        ptype = raw.strip().lower() if isinstance(raw, str) and raw.strip() and "|" not in raw else None
        pages.append((rel, data or {}, items, ptype, text))
    report: dict = {"generated": now_iso(), "engine": ENGINE_VERSION, "roots": proj.roots(), "pages": len(pages),
                    "typed_pages": sum(1 for p in pages if p[3]), "templates": {t: {"file": v["file"], "vocab": v["vocab"]} for t, v in tmpl.items()},
                    "schema": {"file": cfg.get("schema_file"), "vocab": schema["vocab"], "types": schema["types"]},
                    "types": {}, "fields": {}, "scopes": {}, "tags": {}, "relations": {}, "links": {}, "conflicts": [], "unbound_candidates": []}
    obs_types = Counter(p[3] for p in pages if p[3])
    for t in sorted(set(obs_types) | set(tmpl)):
        report["types"][t] = {"pages": obs_types.get(t, 0), "template": tmpl.get(t, {}).get("file"),
                              "declared_in_schema": t in schema["types"] or t in schema["vocab"],
                              "definition": schema["definitions"].get(t) or schema["definitions"].get(t + "s")}
    # observed values per (type, field)
    observed: dict = {}
    for rel, data, items, ptype, _ in pages:
        if not ptype:
            continue
        for it in items:
            observed.setdefault((ptype, it["key"]), Counter())[_unquote(it["raw"])] += 1
    # scope folders
    folders = OrderedDict()
    for r in proj.roots():
        for name, ns in DEFAULT_SCOPE_FOLDERS.items():
            d = root / r / name
            if d.is_dir() and any(x.is_dir() for x in d.iterdir()):
                folders[name] = ns
    report["ids"] = {"scope-folders": folders}
    scope_fields = {}
    for name, ns in folders.items():
        members = OrderedDict()
        for r in proj.roots():
            d = root / r / name
            if d.is_dir():
                for sub in sorted(x for x in d.iterdir() if x.is_dir() and not x.name.startswith(".")):
                    label = None
                    for note in ("README.md", "readme.md", "overview.md", "index.md"):
                        if (sub / note).exists():
                            label = page_title((sub / note).read_text(encoding="utf-8", errors="replace"), sub.name)
                            break
                    members[slugify(sub.name)] = {"folder": f"{r}/{name}/{sub.name}".strip("/"), "label": label}
        field = ns if any(k == ns for (_, k) in observed) or any(ns in v["keys"] for v in tmpl.values()) else None
        schema_vals = []
        for btype, fields in schema["vocab"].items():
            if field and field in fields:
                schema_vals += [v for v in fields[field]["values"] if v not in schema_vals]
        obs = Counter()
        for (_, k), c in observed.items():
            if k == field:
                obs.update(c)
        report["scopes"][ns] = {"folder": name, "field": field, "members": members, "schema_values": schema_vals, "observed": dict(obs)}
        if field:
            scope_fields[field] = ns
    # controlled vocabularies
    type_words = set(report["types"])
    for (ptype, key), counts in sorted(observed.items()):
        if key in scope_fields or key == "type" or key in MULTI_KEYS:
            continue
        values_with_links = sum(c for v, c in counts.items() if WIKILINK_RE.search(v))
        if values_with_links:
            rng = []
            for rel, data, items, pt, _ in pages:
                if pt != ptype:
                    continue
                for it in items:
                    if it["key"] == key:
                        for lm in WIKILINK_RE.finditer(_unquote(it["raw"])):
                            st, c, how = index.resolve(lm.group(1), lm.group(2), type_words)
                            if st in ("ok", "noncanonical") and index.page_type(c[0]):
                                rng.append(index.page_type(c[0]))
            by_name = [t for t in type_words if t in [x.rstrip("s") for x in re.split(r"[-_]", key)]]
            rel_entry = report["relations"].setdefault(slugify(key), {"field": key, "domain": [], "range_resolved": [], "range_from_name": by_name, "values": 0})
            if ptype not in rel_entry["domain"]:
                rel_entry["domain"].append(ptype)
            rel_entry["range_resolved"] = sorted(set(rel_entry["range_resolved"]) | set(rng))
            rel_entry["values"] += values_with_links
            continue
        t_vals = tmpl.get(ptype, {}).get("vocab", {}).get(key)
        s_entry = schema["vocab"].get(ptype, {}).get(key)
        s_vals = s_entry["values"] if s_entry else None
        declared_by = "template" if t_vals else ("schema" if s_vals else None)
        declared = t_vals or s_vals or []
        entry = {"type": ptype, "field": key, "pages": sum(counts.values()), "observed": dict(counts),
                 "template": t_vals, "schema": s_vals, "schema_line": s_entry["line"] if s_entry else None,
                 "declared_by": declared_by, "outside": sorted(v for v in counts if v not in declared)}
        if t_vals and s_vals and [norm(x) for x in t_vals] != [norm(x) for x in s_vals]:
            report["conflicts"].append({"binding": binding_key(ptype, key), "template": t_vals, "schema": s_vals,
                                        "schema_line": s_entry["line"], "note": "template wins by default; decide in the interview"})
        if declared_by:
            report["fields"][binding_key(ptype, key)] = entry
        else:
            distinct = len(counts)
            total = sum(counts.values())
            if total >= 3 and distinct <= max(3, total // 2) and all(len(v) <= 40 and not re.match(r"^\d{4}-\d{2}-\d{2}", v) for v in counts):
                report["unbound_candidates"].append(entry)
    # template vocab for types/fields with no pages yet
    for t, v in tmpl.items():
        for key, vals in v["vocab"].items():
            bk = binding_key(t, key)
            if bk not in report["fields"] and key not in scope_fields:
                report["fields"][bk] = {"type": t, "field": key, "pages": 0, "observed": {}, "template": vals, "schema": None,
                                        "schema_line": None, "declared_by": "template", "outside": []}
    tags = Counter()
    for rel, data, items, ptype, _ in pages:
        for it in items:
            if it["key"] == "tags":
                raw = _unquote(it["raw"])
                parts = [p for _, _, p in split_comma_tokens(raw)] if ("," in raw and not it["raw"].startswith(("'", '"'))) else [raw]
                tags.update(p for p in parts if p)
    report["tags"] = dict(sorted(tags.items(), key=lambda x: (-x[1], x[0])))
    lstats = Counter()
    for rel, data, items, ptype, text in pages:
        _, _, body_at = frontmatter_items(text)
        for lm in WIKILINK_RE.finditer(visible_body(text[body_at:])):
            st, c, how = index.resolve(lm.group(1), lm.group(2), type_words)
            lstats[st] += 1
    report["links"] = dict(lstats)
    return report


# ----------------------------------------------------------------------------- init: building the ontology

def _leaf(value: str) -> str:
    return EMOJI_LEAVES.get(value) or slugify(value) or "u" + "-".join(f"{ord(c):x}" for c in value)[:40]


def _glob_any(tid: str, patterns) -> bool:
    return any(fnmatch.fnmatchcase(tid, p) for p in as_list(patterns))


def build_ontology(report: dict, decisions: dict, by: str | None, existing: Ontology | None = None) -> tuple[dict, dict]:
    """Defaults: declared (template / SCHEMA.md / scope folder) → approved; observed-only → proposed;
    spelling variants of an approved term → proposed alias. Decisions (from the interview) override.
    With an existing ontology, only additions are made — nothing already declared is changed."""
    d = decisions or {}
    stamp = today()
    data: dict = OrderedDict()
    if existing is not None:
        data = existing.data
    else:
        data["version"] = 1
        data["name"] = d.get("name") or "project-ontology"
        data["policy"] = OrderedDict([("default", "strict"), ("proposed", "warn"), ("approval", "human"),
                                      ("overrides", OrderedDict([("tag", "warn")]))])
        data["ids"] = OrderedDict([("scope-folders", OrderedDict(report.get("ids", {}).get("scope-folders", {}))),
                                   ("folder-notes", list(DEFAULT_FOLDER_NOTES)), ("ignore-types", list(DEFAULT_IGNORE_TYPES))])
        data["fields"] = OrderedDict()
        for sec in SECTIONS:
            data[sec] = OrderedDict()
    data["updated"] = stamp
    if isinstance(d.get("policy"), dict):
        pol = data.setdefault("policy", OrderedDict())
        for k, v in d["policy"].items():
            pol[k] = v
    added = Counter()

    def put(section, tid, attrs):
        if tid in data[section]:
            return False
        for sec in SECTIONS:
            if tid in data[sec]:
                return False
        data[section][tid] = attrs
        added[section] += 1
        return True

    def status_attrs(declared: bool, source: str) -> OrderedDict:
        """Declared values are approved by the people who declared them (template, SCHEMA.md, folder
        layout) — the record says so. Observed-only values are proposed: nothing is silently approved."""
        a = OrderedDict([("status", "approved" if declared else "proposed"), ("since", stamp), ("source", source)])
        if declared:
            a["approved-by"] = "declared in source"
            a["approved-on"] = stamp
        return a

    ignore = set(DEFAULT_IGNORE_TYPES)
    # types
    for t, info in report.get("types", {}).items():
        declared = bool(info.get("template") or info.get("declared_in_schema") or t in ignore)
        src = (f"template {info['template']}" if info.get("template") else "SCHEMA.md" if info.get("declared_in_schema")
               else "structural type" if t in ignore else f"observed on {info.get('pages', 0)} page(s)")
        a = OrderedDict([("label", t.replace("-", " ").title())])
        if slugify(t) != t:
            a["value"] = t
        if info.get("definition"):
            a["definition"] = info["definition"]
        a.update(status_attrs(declared, src))
        put("types", f"type.{slugify(t)}", a)
    if "*.type" not in data["fields"]:
        data["fields"]["*.type"] = OrderedDict([("kind", "type")])
    # vocabularies
    for bkey, f in report.get("fields", {}).items():
        choice = (d.get("vocab_source") or {}).get(bkey, "template")
        tvals, svals = f.get("template") or [], f.get("schema") or []
        if choice == "schema" and svals:
            declared, src = svals, "SCHEMA.md"
        elif choice == "union":
            declared, src = list(dict.fromkeys(list(tvals) + [v for v in svals if norm(v) not in {norm(x) for x in tvals}])), "template + SCHEMA.md"
        else:
            declared, src = (tvals, f"template") if tvals else (svals, "SCHEMA.md")
        if bkey in (d.get("unbind") or []):
            continue
        tp = slugify(f["type"])
        fieldseg = slugify(f["field"])
        if bkey not in data["fields"]:
            data["fields"][bkey] = OrderedDict([("kind", "vocab")])
        canon_by_norm = {}
        for v in declared:
            tid = f"{tp}.{fieldseg}.{_leaf(v)}"
            a = OrderedDict([("label", v)])
            if _leaf(v) != v:
                a["value"] = v
            a.update(status_attrs(True, f"{src} ({report.get('templates', {}).get(f['type'], {}).get('file') or report.get('schema', {}).get('file')})"))
            put("vocabularies", tid, a)
            canon_by_norm[norm(v)] = tid
        for v, n in sorted(f.get("observed", {}).items()):
            if v in declared:
                continue
            if norm(v) in canon_by_norm:
                tid = canon_by_norm[norm(v)]
                term = data["vocabularies"].get(tid)
                if term is not None and v not in as_list(term.get("proposed-aliases")) and v not in as_list(term.get("aliases")):
                    term["proposed-aliases"] = as_list(term.get("proposed-aliases")) + [v]
                    added["proposed-aliases"] += 1
                continue
            tid = f"{tp}.{fieldseg}.{_leaf(v)}"
            a = OrderedDict([("label", v)])
            if _leaf(v) != v:
                a["value"] = v
            a.update(status_attrs(False, f"observed on {n} page(s)"))
            put("vocabularies", tid, a)
    for cand in report.get("unbound_candidates", []):
        bkey = binding_key(cand["type"], cand["field"])
        if (d.get("bind") or {}).get(bkey) == "vocab":
            data["fields"].setdefault(bkey, OrderedDict([("kind", "vocab")]))
            for v, n in sorted(cand["observed"].items()):
                a = OrderedDict([("label", v)])
                if _leaf(v) != v:
                    a["value"] = v
                a.update(status_attrs(False, f"observed on {n} page(s)"))
                put("vocabularies", f"{slugify(cand['type'])}.{slugify(cand['field'])}.{_leaf(v)}", a)
    # scopes → entities. A folder note's title ("# Northwind Traders", "# MerchTank — overview") is
    # evidence of the entity's display name, so a page writing that name is a spelling of the entity,
    # not a new one.
    for ns, s in report.get("scopes", {}).items():
        members = s.get("members", {})
        spellings: dict[str, str] = {}
        for slug, m in members.items():
            title = (m.get("label") or "").strip()
            head = re.split(r"\s+[—–|:-]\s+|:\s+", title, maxsplit=1)[0].strip() if title else ""
            for cand in (title, head):
                if cand:
                    spellings.setdefault(norm(cand), slug)
            observed_name = next((v for v in s.get("observed", {}) if norm(v) != slug and spellings.get(norm(v)) == slug), None)
            label = observed_name or (head if head and norm(head) == slug else None) or slug.replace("-", " ").title()
            a = OrderedDict([("label", label)])
            a.update(status_attrs(True, f"folder {m.get('folder')}"))
            put("entities", f"{ns}.{slug}", a)
        for v in s.get("schema_values", []):
            if norm(v) not in members:
                a = OrderedDict([("label", v.replace("-", " ").title())])
                if _leaf(v) != v:
                    a["value"] = v
                a.update(status_attrs(True, "SCHEMA.md"))
                put("entities", f"{ns}.{_leaf(v)}", a)
        if s.get("field"):
            data["fields"].setdefault(binding_key("*", s["field"]), OrderedDict([("kind", "entity"), ("namespace", ns)]))
        known = {k: f"{ns}.{slug}" for k, slug in spellings.items()}
        known.update({norm(slug): f"{ns}.{slug}" for slug in members})
        known.update({norm(v): f"{ns}.{_leaf(v)}" for v in s.get("schema_values", [])})
        for v, n in sorted(s.get("observed", {}).items()):
            tid = known.get(norm(v))
            if tid and tid in data["entities"]:
                term = data["entities"][tid]
                if v != term_value(dict(term, _id=tid, _kind="entity")) and v not in as_list(term.get("aliases")) + as_list(term.get("proposed-aliases")):
                    term["proposed-aliases"] = as_list(term.get("proposed-aliases")) + [v]
                    added["proposed-aliases"] += 1
                continue
            a = OrderedDict([("label", v)])
            if _leaf(v) != v:
                a["value"] = v
            a.update(status_attrs(False, f"observed on {n} page(s)"))
            put("entities", f"{ns}.{_leaf(v)}", a)
    # tags
    if report.get("tags"):
        data["fields"].setdefault("*.tags", OrderedDict([("kind", "tag")]))
    for tag, n in report.get("tags", {}).items():
        segs = [slugify(p) for p in str(tag).split("/")]
        tid = "tag." + (".".join(segs) if all(segs) else (slugify(tag) or _leaf(tag)))
        a = OrderedDict()
        expected_value = "/".join(tid.split(".")[1:])
        if expected_value != tag:
            if tid in data["tags"]:
                term = data["tags"][tid]
                if tag not in as_list(term.get("proposed-aliases")) + as_list(term.get("aliases")):
                    term["proposed-aliases"] = as_list(term.get("proposed-aliases")) + [tag]
                continue
            a["value"] = tag
        a.update(status_attrs(False, f"observed on {n} page(s)"))
        put("tags", tid, a)
    # relations
    for name, r in report.get("relations", {}).items():
        # a field that names its target type (`related-feature`) states its range; observed targets
        # would also absorb the very mistakes the relation exists to catch
        rng = r.get("range_from_name") or r.get("range_resolved") or []
        rid = f"rel.{name}"
        a = OrderedDict([("label", r["field"].replace("-", " ").replace("_", " ").capitalize()), ("domain", r["domain"]), ("range", rng)])
        a.update(status_attrs(False, f"frontmatter links on {r.get('values', 0)} value(s); range from " + ("the field name" if r.get("range_from_name") else "resolved targets")))
        put("relations", rid, a)
        for dt in r["domain"]:
            data["fields"].setdefault(binding_key(dt, r["field"]), OrderedDict([("kind", "relation"), ("relation", rid)]))
    # interview decisions
    for sec in SECTIONS:
        for tid, attrs in data[sec].items():
            if _glob_any(tid, d.get("approve")) and attrs.get("status") != "approved":
                attrs["status"], attrs["approved-by"], attrs["approved-on"] = "approved", by or "interview", stamp
            if _glob_any(tid, d.get("propose")):
                attrs["status"] = "proposed"
                attrs.pop("approved-by", None)
                attrs.pop("approved-on", None)
            if _glob_any(tid, d.get("approve_aliases")) and attrs.get("proposed-aliases"):
                attrs["aliases"] = as_list(attrs.get("aliases")) + as_list(attrs.pop("proposed-aliases"))
            if tid in (d.get("aliases") or {}):
                for al in as_list(d["aliases"][tid]):
                    if al not in as_list(attrs.get("aliases")):
                        attrs["aliases"] = as_list(attrs.get("aliases")) + [al]
                    if al in as_list(attrs.get("proposed-aliases")):
                        attrs["proposed-aliases"] = [x for x in as_list(attrs["proposed-aliases"]) if x != al]
            if tid in (d.get("deprecate") or {}):
                attrs["status"], attrs["deprecated-by"], attrs["deprecated-on"] = "deprecated", by or "interview", stamp
                if d["deprecate"][tid]:
                    attrs["replaced-by"] = d["deprecate"][tid]
            if tid in (d.get("labels") or {}):
                attrs["label"] = d["labels"][tid]
            if tid in (d.get("definitions") or {}):
                attrs["definition"] = d["definitions"][tid]
    for tid, attrs in (d.get("terms") or {}).items():
        sec = attrs.pop("section", None) or ("types" if tid.startswith("type.") else "tags" if tid.startswith("tag.") else "relations" if tid.startswith("rel.") else "vocabularies" if tid.count(".") == 2 else "entities")
        put(sec, tid, OrderedDict(attrs))
    for bkey, spec in (d.get("fields") or {}).items():
        data["fields"][bkey] = OrderedDict(spec)
    return data, dict(added)


def classify_observed(report: dict, onto: Ontology) -> dict:
    """Every observed controlled value → approved | proposed | noncanonical | deprecated | unknown."""
    out = Counter()
    unknown = []
    for bkey, f in report.get("fields", {}).items():
        b = onto.fields.get(bkey)
        if not b:
            continue
        for v in f.get("observed", {}):
            t, how = onto.match("vocab", bkey, v)
            key = "unknown" if t is None else ("noncanonical" if how != "canonical" else t.get("status"))
            out[key] += 1
            if t is None:
                unknown.append(f"{bkey}: {v}")
    for ns, s in report.get("scopes", {}).items():
        for v in s.get("observed", {}):
            t, how = onto.match("entity", ns, v)
            out["unknown" if t is None else ("noncanonical" if how != "canonical" else t.get("status"))] += 1
            if t is None:
                unknown.append(f"{ns}: {v}")
    for tag in report.get("tags", {}):
        t, how = onto.match("tag", None, tag)
        out["unknown" if t is None else ("noncanonical" if how != "canonical" else t.get("status"))] += 1
        if t is None:
            unknown.append(f"tag: {tag}")
    for tname in report.get("types", {}):
        t, how = onto.match("type", "type", tname)
        out["unknown" if t is None else t.get("status")] += 1
        if t is None:
            unknown.append(f"type: {tname}")
    return {"counts": dict(out), "unknown": unknown}


# ----------------------------------------------------------------------------- render

def _cell(s) -> str:
    return str(s if s not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def _alias_cell(t: dict) -> str:
    parts = []
    if as_list(t.get("aliases")):
        parts.append(", ".join(f"`{a}`" for a in as_list(t.get("aliases"))))
    if as_list(t.get("proposed-aliases")):
        parts.append("proposed: " + ", ".join(f"`{a}`" for a in as_list(t.get("proposed-aliases"))))
    return " · ".join(parts)


def render_doc(proj: Project) -> str:
    onto, cfg = proj.onto, proj.config
    tc = term_counts(onto)
    ov = ", ".join(f"{k}: {v}" for k, v in onto.overrides.items()) or "none"
    L = [f"<!-- generated by project-ontology from {Path(cfg['ontology_file']).name} — do not edit here; edit the ontology with /ontology:propose · approve · deprecate -->",
         f"# Ontology — {onto.data.get('name') or 'project'}", "",
         f"> {tc['terms']} terms · {tc['approved']} approved · {tc['proposed']} proposed · {tc['deprecated']} deprecated · "
         f"policy **{onto.policy_default}** (overrides: {ov}; proposed terms: {onto.policy_proposed}) · approval: **{onto.approval}** · updated {onto.data.get('updated') or '—'}", "",
         "## How to use this", "",
         "- **Pages keep plain values** (`severity: critical`). This file lists which plain values are legal for each controlled field; the dot-notated id (`gap.severity.critical`) is how the database, error messages and discussions name the term.",
         "- **Use an approved value.** A write that adds an unregistered, deprecated or misspelled value is blocked by the PreToolUse hook (strict policy); values already on a page before the edit do not block (ratchet).",
         f"- **New concept?** Register it before use: `{ENGINE_CMD} propose <id> --label … --definition …`. Proposed terms are usable at once and flagged until a human approves them (`/ontology:approve`).",
         "- **Links** must resolve to exactly one page: `[[slug]]`, or `[[folder/slug]]` when two pages share a slug. `[[type|slug]]` and title-only links are noncanonical.",
         f"- **Page ids are derived, never written:** `{'/'.join(list(onto.scope_folders)[:1] or ['clients'])}/<scope>/<folder>/<file>.md` with `type: gap` → `{(list(onto.scope_folders.values()) or ['client'])[0]}.<scope>.gap.<file>`; a folder note ({', '.join(onto.folder_notes)}) is the scope entity itself; pages outside a scope folder are `<type>.<file>`.",
         "", "## Controlled fields", "", "| Binding | Field | Kind | Approved values |", "|---|---|---|---|"]
    for bkey, spec in onto.fields.items():
        kind = spec.get("kind")
        tp, fld = bkey.split(".", 1)
        if kind == "vocab":
            parent = bkey if tp != "*" else None
            vals = [term_value(t) for t in onto.terms.values() if t["_kind"] == "vocab" and parent and term_parent(t) == parent and t.get("status") == "approved"]
            allowed = " · ".join(f"`{v}`" for v in vals) or "—"
        elif kind == "entity":
            ns = spec.get("namespace")
            vals = [term_value(t) for t in onto.terms.values() if t["_kind"] == "entity" and term_parent(t) == ns and t.get("status") == "approved"]
            allowed = f"entities `{ns}.*`: " + (" · ".join(f"`{v}`" for v in vals) or "—")
        elif kind == "tag":
            allowed = "`tag.*` (see Tags)"
        elif kind == "type":
            allowed = " · ".join(f"`{term_value(t)}`" for t in onto.terms.values() if t["_kind"] == "type" and t.get("status") == "approved")
        else:
            rel = onto.terms.get(spec.get("relation") or "", {})
            allowed = f"[[links]] to {'|'.join(as_list(rel.get('range'))) or 'any'} pages (`{spec.get('relation')}`)"
        L.append(f"| `{bkey}` | `{fld}` | {kind} | {_cell(allowed)} |")
    L += ["", "## Types", "", "| Id | Value | Status | Definition |", "|---|---|---|---|"]
    for t in onto.terms.values():
        if t["_kind"] == "type":
            L.append(f"| `{t['_id']}` | `{term_value(t)}` | {t.get('status')} | {_cell(t.get('definition'))} |")
    L += ["", "## Vocabularies", ""]
    parents = OrderedDict()
    for t in onto.terms.values():
        if t["_kind"] == "vocab":
            parents.setdefault(term_parent(t), []).append(t)
    for parent, terms in parents.items():
        tp, fld = parent.split(".", 1)
        L += [f"### `{parent}` — `{fld}:` on {tp} pages", "", "| Value | Id | Status | Aliases | Definition |", "|---|---|---|---|---|"]
        for t in terms:
            al = _alias_cell(t)
            st = t.get("status") + (f" → `{t['replaced-by']}`" if t.get("replaced-by") else "")
            L.append(f"| `{term_value(t)}` | `{t['_id']}` | {st} | {_cell(al)} | {_cell(t.get('definition'))} |")
        L.append("")
    ents = [t for t in onto.terms.values() if t["_kind"] == "entity"]
    if ents:
        L += ["## Entities", "", "| Value | Id | Label | Status | Aliases |", "|---|---|---|---|---|"]
        for t in ents:
            al = _alias_cell(t)
            L.append(f"| `{term_value(t)}` | `{t['_id']}` | {_cell(t.get('label'))} | {t.get('status')} | {_cell(al)} |")
        L.append("")
    rels = [t for t in onto.terms.values() if t["_kind"] == "relation"]
    if rels:
        L += ["## Relations", "", "| Id | Fields | Domain | Range | Status |", "|---|---|---|---|---|"]
        for t in rels:
            fields = ", ".join(f"`{k}`" for k, s in onto.fields.items() if s.get("relation") == t["_id"])
            L.append(f"| `{t['_id']}` | {fields or '—'} | {', '.join(as_list(t.get('domain'))) or '—'} | {', '.join(as_list(t.get('range'))) or '—'} | {t.get('status')} |")
        L.append("")
    tags = [t for t in onto.terms.values() if t["_kind"] == "tag"]
    if tags:
        L += ["## Tags", ""]
        for st in STATUSES:
            group = [t for t in tags if t.get("status") == st]
            if group:
                L.append(f"**{st.capitalize()} ({len(group)}):** " + " · ".join(f"`{term_value(t)}`" for t in group))
                L.append("")
    dep = [t for t in onto.terms.values() if t.get("status") == "deprecated"]
    if dep:
        L += ["## Deprecated", "", "| Id | Replaced by | Reason |", "|---|---|---|"]
        for t in dep:
            L.append(f"| `{t['_id']}` | {_cell(t.get('replaced-by'))} | {_cell(t.get('reason'))} |")
        L.append("")
    L += ["## Commands", "", "| Situation | Command |", "|---|---|",
          "| Check pages / the whole vault | `/ontology:check [<path>\\|--all]` |",
          "| A value you need is not registered | `/ontology:propose <id> --label … --definition …` |",
          "| Approve proposed terms (human) | `/ontology:approve <id>…` |",
          "| Retire a term | `/ontology:deprecate <id> --replaced-by <id>` |",
          "| Rewrite aliases / deprecated values / noncanonical links | `/ontology:apply --dry-run`, then `/ontology:apply` |",
          "| Counts, open violations, pending approvals | `/ontology:status` |"]
    if onto.errors:
        L += ["", "## ⚠ Ontology errors", ""] + [f"- {e}" for e in onto.errors]
    return "\n".join(L) + "\n"


def sync_templates(proj: Project, dry_run: bool = False) -> list[str]:
    """`key:` lines of page templates carry their binding: `severity: # gap.severity: critical|high|medium|low`."""
    tdir = proj.config.get("templates_dir")
    changed = []
    if not tdir or not (proj.root / tdir).is_dir():
        return changed
    onto = proj.onto
    for p in sorted((proj.root / tdir).glob("*.md")):
        text = p.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        if not m:
            continue
        data, _ = parse_frontmatter(m.group(1))
        t = data.get("type")
        ptype = str(t).strip().lower() if isinstance(t, str) and t.strip() and "|" not in t else p.stem.lower()
        lines = m.group(1).split("\n")
        new_lines = []
        for ln in lines:
            km = KEY_LINE_RE.match(ln)
            if km and km.group(1) != "type":
                val, _c = _strip_comment(ln[len(km.group(1)) + 1:])
                b = onto.binding(ptype, km.group(1))
                if b and val.strip() == "":
                    bkey, spec = b
                    kind = spec.get("kind")
                    comment = None
                    if kind == "vocab":
                        parent = bkey if not bkey.startswith("*.") else f"{slugify(ptype)}.{bkey.split('.', 1)[1]}"
                        vals = [term_value(x) for x in onto.terms.values() if x["_kind"] == "vocab" and term_parent(x) == parent and x.get("status") == "approved"]
                        comment = f"{parent}: {'|'.join(vals)}" if vals else None
                    elif kind == "entity":
                        comment = f"{spec.get('namespace')}.*"
                    elif kind == "tag":
                        comment = "tag.*"
                    elif kind == "relation":
                        rel = onto.terms.get(spec.get("relation") or "", {})
                        comment = f"{spec.get('relation')} → {'|'.join(as_list(rel.get('range'))) or 'page'}"
                    if comment:
                        ln = f"{km.group(1)}: # {comment}"
            new_lines.append(ln)
        new = text[:m.start(1)] + "\n".join(new_lines) + text[m.end(1):]
        if new != text:
            changed.append(rel_posix(p, proj.root) or str(p))
            if not dry_run:
                p.write_text(new, encoding="utf-8")
    return changed


def render_all(proj: Project, templates: bool = False) -> dict:
    out = {}
    doc = proj.config.get("doc_file")
    if doc:
        target = proj.root / doc
        target.parent.mkdir(parents=True, exist_ok=True)
        text = render_doc(proj)
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            target.write_text(text, encoding="utf-8")
            out["doc"] = "updated"
        else:
            out["doc"] = "unchanged"
    if templates:
        out["templates"] = sync_templates(proj)
    return out


# ----------------------------------------------------------------------------- install

def merge_managed_block(path: Path, block: str) -> str:
    block = block.rstrip("\n")
    wrapped = f"{SENTINEL_OPEN}\n{block}\n{SENTINEL_CLOSE}"
    if not path.exists():
        path.write_text(wrapped + "\n", encoding="utf-8")
        return "created"
    text = path.read_text(encoding="utf-8")
    if SENTINEL_OPEN in text and SENTINEL_CLOSE in text:
        pre, rest = text.split(SENTINEL_OPEN, 1)
        _, post = rest.split(SENTINEL_CLOSE, 1)
        new = pre + wrapped + post
        if new == text:
            return "unchanged"
        path.write_text(new, encoding="utf-8")
        return "updated"
    sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    path.write_text(text + sep + wrapped + "\n", encoding="utf-8")
    return "updated"


def merge_json_file(path: Path, mutate) -> str:
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError as e:
            die(f"{path} is not valid JSON ({e}); fix it before installing")
    before = json.dumps(data, sort_keys=True)
    mutate(data)
    after = json.dumps(data, sort_keys=True)
    if before == after and path.exists():
        return "unchanged"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return "updated" if before != "{}" else "created"


# "$CLAUDE_PROJECT_DIR" is quoted: an unquoted project path containing a space makes the command exit 127,
# which Claude Code treats as a non-blocking hook error — enforcement would silently stop.
HOOK_ENTRIES = [
    ("PreToolUse", "Write|Edit|MultiEdit", f'"$CLAUDE_PROJECT_DIR"/{GUARD_HOOK_REL} pre', 20),
    ("PreToolUse", "Bash", f'"$CLAUDE_PROJECT_DIR"/{GUARD_HOOK_REL} bash', 10),
    ("PostToolUse", "Write|Edit|MultiEdit", f'"$CLAUDE_PROJECT_DIR"/{GUARD_HOOK_REL} post', 20),
    ("SessionStart", None, f'"$CLAUDE_PROJECT_DIR"/{CONTEXT_HOOK_REL}', 30),
]


def install(proj: Project, skill_dir: Path) -> dict:
    root, cfg = proj.root, proj.config
    tpl = skill_dir / "templates"
    if not (tpl / "ontology-guard.sh").exists():
        die(f"skill templates not found under {tpl} — pass --skill-dir <path to skills/project-ontology>")
    report = {}
    odir = root / ONTO_DIR_REL
    odir.mkdir(parents=True, exist_ok=True)
    src, dst = Path(__file__).resolve(), (odir / "ontology.py").resolve()
    if src != dst:
        shutil.copy2(src, dst)
        report["engine"] = f"vendored v{ENGINE_VERSION}"
    for name, rel in (("ontology-guard.sh", GUARD_HOOK_REL), ("ontology-context.sh", CONTEXT_HOOK_REL)):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tpl / name, target)
        target.chmod(0o755)

    def add_hooks(settings):
        hooks = settings.setdefault("hooks", {})
        for event, matcher, command, timeout in HOOK_ENTRIES:
            lst = hooks.setdefault(event, [])
            marker = command.split("/")[-1]
            found = False
            for e in lst:
                for h in e.get("hooks", []):
                    if marker in h.get("command", ""):
                        found = True
                        h["command"] = command  # upgrade an older (unquoted) entry in place
            if found:
                continue
            entry = {"hooks": [{"type": "command", "command": command, "timeout": timeout}]}
            if matcher:
                entry = {"matcher": matcher, **entry}
            lst.append(entry)

    report["settings.json"] = merge_json_file(root / ".claude/settings.json", add_hooks)
    block_tpl = (tpl / ("claude-md-block.wiki.md" if cfg.get("has_wiki") else "claude-md-block.standalone.md")).read_text(encoding="utf-8")
    block = (block_tpl.replace("{{ONTOLOGY_FILE}}", cfg["ontology_file"]).replace("{{DOC_FILE}}", cfg.get("doc_file") or cfg["ontology_file"])
             .replace("{{ROOTS}}", ", ".join(f"`{r}/`" for r in proj.roots())).replace("{{ENGINE}}", ENGINE_CMD))
    report["CLAUDE.md"] = merge_managed_block(root / "CLAUDE.md", block)
    gi = root / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    want = ["# project-ontology: caches and interview scratch (regenerated)", f"{STATE_REL}", f"{REPORT_REL}", f"{ONTO_DIR_REL}/decisions.json"]
    if not any(STATE_REL in ln for ln in lines):
        gi.write_text("\n".join(lines + ([""] if lines and lines[-1] else []) + want) + "\n", encoding="utf-8")
        report[".gitignore"] = "updated"
    return report


def default_config(root: Path, wiki: str | None, roots: list[str], exclude: list[str]) -> dict:
    if wiki:
        return {"engine_version": ENGINE_VERSION, "has_wiki": True, "roots": [wiki],
                "exclude": exclude or ["_schema/*", "_lint-report-*"], "link_exclude": list(DEFAULT_LINK_EXCLUDE),
                "ontology_file": f"{wiki}/_schema/ontology.yaml", "doc_file": f"{wiki}/_schema/ONTOLOGY.md",
                "templates_dir": f"{wiki}/_schema/templates" if (root / wiki / "_schema" / "templates").is_dir() else None,
                "schema_file": f"{wiki}/_schema/SCHEMA.md" if (root / wiki / "_schema" / "SCHEMA.md").exists() else None,
                "log_file": f"{wiki}/_log.md" if (root / wiki / "_log.md").exists() else None}
    return {"engine_version": ENGINE_VERSION, "has_wiki": False, "roots": roots, "exclude": exclude,
            "ontology_file": f"{ONTO_DIR_REL}/ontology.yaml", "doc_file": f"{ONTO_DIR_REL}/ONTOLOGY.md",
            "templates_dir": None, "schema_file": None, "log_file": f"{ONTO_DIR_REL}/LOG.md"}


def append_log(proj: Project, title: str, body: str) -> None:
    log_rel = proj.config.get("log_file")
    if not log_rel:
        return
    target = proj.root / log_rel
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"---\ntype: log\nupdated: {today()}\n---\n\n# project-ontology Operation Log\n\n", encoding="utf-8")
    text = target.read_text(encoding="utf-8")
    text = text.rstrip("\n") + "\n" + f"\n## {today()} — {title}\n\n{body.strip()}\n"
    m = FM_RE.match(text)
    if m and re.search(r"(?m)^updated:", m.group(1)):  # keep the log page's own `updated:` true
        fm = re.sub(r"(?m)^updated:.*$", f"updated: {today()}", m.group(1), count=1)
        text = text[:m.start(1)] + fm + text[m.end(1):]
    target.write_text(text, encoding="utf-8")


# ----------------------------------------------------------------------------- state cache (banner speed)

def fingerprint(proj: Project) -> str:
    h = hashlib.sha256()
    h.update(ENGINE_VERSION.encode())
    try:
        h.update(Path(__file__).read_bytes())  # an edited or re-vendored engine never serves a stale cached check
    except OSError:
        pass
    for p in (proj.ontology_path, proj.root / CONFIG_REL):
        try:
            h.update(p.read_bytes())
        except OSError:
            pass
    for r in proj.roots():
        base = proj.root / r
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for fn in sorted(filenames):
                p = Path(dirpath) / fn
                try:
                    st = p.stat()
                except OSError:
                    continue
                h.update(f"{rel_posix(p, proj.root)}:{st.st_size}:{st.st_mtime_ns}\n".encode())
    return h.hexdigest()


def cached_check(proj: Project) -> tuple[list[dict], dict[str, dict]]:
    fp = fingerprint(proj)
    sp = proj.root / STATE_REL
    try:
        st = json.loads(sp.read_text(encoding="utf-8"))
        if st.get("fingerprint") == fp:
            return st["violations"], st["pages"]
    except (OSError, ValueError, KeyError):
        pass
    viols, pages = check_all(proj)
    try:
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps({"fingerprint": fp, "at": now_iso(), "violations": viols, "pages": pages}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return viols, pages


# ----------------------------------------------------------------------------- project-db API

def load_for_db(root: Path) -> dict | None:
    """What project-db materializes at sync: terms, aliases, field bindings, page ids, violations.
    None when the project has no ontology; {"error": …} when it cannot be loaded."""
    proj = Project.load(root, require=False)
    if proj is None:
        return None
    if proj.onto is None:
        return {"api": API_VERSION, "error": proj.onto_error, "file": proj.config.get("ontology_file")}
    onto = proj.onto
    viols, pages = cached_check(proj)
    terms, aliases = [], []
    for t in onto.terms.values():
        terms.append({"id": t["_id"], "kind": t["_kind"], "namespace": t["_id"].split(".")[0], "parent": term_parent(t),
                      "value": term_value(t) if t["_kind"] != "relation" else None, "label": t.get("label"),
                      "definition": t.get("definition"), "status": t.get("status"), "replaced_by": t.get("replaced-by"),
                      "since": t.get("since"), "approved_by": t.get("approved-by"), "approved_on": t.get("approved-on"),
                      "source": t.get("source"), "domain": ",".join(map(str, as_list(t.get("domain")))) or None,
                      "range": ",".join(map(str, as_list(t.get("range")))) or None})
        for a in as_list(t.get("aliases")):
            aliases.append({"alias": str(a), "term_id": t["_id"], "status": "approved"})
        for a in as_list(t.get("proposed-aliases")):
            aliases.append({"alias": str(a), "term_id": t["_id"], "status": "proposed"})
    fields = []
    for bkey, spec in onto.fields.items():
        tp, fld = bkey.split(".", 1)
        fields.append({"binding": bkey, "type": tp, "field": fld, "kind": spec.get("kind"),
                       "namespace": spec.get("namespace"), "relation": spec.get("relation")})
    return {"api": API_VERSION, "engine": ENGINE_VERSION, "file": proj.config["ontology_file"], "roots": proj.roots(),
            "policy": {"default": onto.policy_default, "overrides": onto.overrides, "approval": onto.approval},
            "terms": terms, "aliases": aliases, "fields": fields, "pages": pages, "violations": viols,
            "summary": dict(summarize(viols), **term_counts(onto)), "errors": onto.errors}


# ----------------------------------------------------------------------------- apply

def _format_value(new: str, original_raw: str, in_list: bool) -> str:
    if original_raw[:1] in "\"'" and original_raw[-1:] == original_raw[:1]:
        q = original_raw[0]
        return q + (new.replace("'", "''") if q == "'" else new.replace('"', '\\"')) + q
    risky = (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _./()+\-]*", new) or new.lower() in ("true", "false", "yes", "no", "null")
             or re.fullmatch(r"-?\d+(\.\d+)?", new) or (in_list and "," in new))
    return json.dumps(new, ensure_ascii=False) if risky else new


def plan_rewrites(proj: Project, rel: str, text: str, index: FileIndex) -> list[dict]:
    """Mechanical fixes only: aliases / spelling variants → canonical value, deprecated values → their
    replacement, noncanonical links → the canonical target. Judgment calls stay violations."""
    edits = []
    for v in check_text(proj, rel, text, index):
        if v["rule"] in ("value-noncanonical", "value-deprecated", "type-deprecated") and v.get("replacement") and v.get("start") is not None:
            raw = text[v["start"]:v["end"]]
            in_list = raw != text[v["start"]:v["end"]] or text[max(0, v["start"] - 1)] in "[, "
            edits.append({"start": v["start"], "end": v["end"], "old": raw, "new": _format_value(v["replacement"], raw, in_list),
                          "rule": v["rule"], "line": v.get("line"), "field": v.get("field")})
        elif v["rule"] in ("link-noncanonical", "relation-noncanonical") and v.get("replacement") and v.get("start") is not None:
            edits.append({"start": v["start"], "end": v["end"], "old": v["value"], "new": v["replacement"],
                          "rule": v["rule"], "line": v.get("line"), "field": v.get("field")})
    return edits


def apply_rewrites(text: str, edits: list[dict]) -> str:
    """Span edits only, applied back to front; an edit whose span no longer holds the text it expects is
    skipped. The same link text inside code or an HTML comment is never touched."""
    for e in sorted(edits, key=lambda e: -e["start"]):
        if text[e["start"]:e["end"]] == e["old"]:
            text = text[:e["start"]] + e["new"] + text[e["end"]:]
    return text


# ----------------------------------------------------------------------------- governance writes

def save_ontology(proj: Project, data: dict) -> Ontology:
    text = dump_onto_yaml(data)
    onto = Ontology(parse_onto_yaml(text))
    proj.ontology_path.parent.mkdir(parents=True, exist_ok=True)
    proj.ontology_path.write_text(text, encoding="utf-8")
    proj.onto = onto
    render_all(proj, templates=False)
    return onto


def _kind_for_new_id(onto: Ontology, tid: str, kind: str | None) -> str:
    if kind:
        return kind
    segs = tid.split(".")
    if segs[0] == "type":
        return "type"
    if segs[0] == "tag":
        return "tag"
    if segs[0] == "rel":
        return "relation"
    types = {t["_id"].split(".", 1)[1] for t in onto.terms.values() if t["_kind"] == "type"}
    if len(segs) == 3 and segs[0] in types:
        return "vocab"
    namespaces = {str(s.get("namespace")) for s in onto.fields.values() if s.get("kind") == "entity"} | set(onto.scope_folders.values()) \
        | {term_parent(t) for t in onto.terms.values() if t["_kind"] == "entity"}
    if len(segs) == 2 and segs[0] in namespaces:
        return "entity"
    die(f"cannot tell what kind of term `{tid}` is — vocabulary ids are `<declared type>.<field>.<value>` "
        f"(declared types: {', '.join(sorted(types)) or 'none'}), entity ids `<namespace>.<slug>` (namespaces: "
        f"{', '.join(sorted(n for n in namespaces if n and n != 'None')) or 'none'}), or pass --kind")
    return ""


# ----------------------------------------------------------------------------- commands

def _cli_rel(proj: Project, p: str) -> str | None:
    """A path given on the command line: absolute, relative to the cwd, or relative to the project root."""
    path = Path(p)
    if path.is_absolute():
        return rel_posix(path, proj.root)
    for base in (Path.cwd(), proj.root):
        if (base / path).exists():
            return rel_posix(base / path, proj.root)
    return rel_posix(proj.root / path, proj.root)


def _load(a) -> Project:
    root = find_root(Path(a.root)) if getattr(a, "root", None) else find_root()
    proj = Project.load(root)
    if proj.onto is None and a.cmd not in ("install",):
        die(proj.onto_error or "ontology not loaded")
    return proj


def cmd_init(a):
    root = Path(a.root or ".").resolve()
    skill_dir = Path(a.skill_dir).resolve() if a.skill_dir else Path(__file__).resolve().parent.parent
    cfg_path = root / CONFIG_REL
    if cfg_path.exists() and not a.force_config:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    else:
        wiki = None if a.no_wiki else (a.wiki_root or detect_wiki(root))
        roots = a.govern or []
        if not wiki and not roots:
            db_cfg = root / ".claude/db/config.json"
            if db_cfg.exists():
                roots = [c.get("root", ".") for c in json.loads(db_cfg.read_text(encoding="utf-8")).get("collections", []) if c.get("kind", "markdown") == "markdown"]
        if not wiki and not roots:
            die("no wiki found and no --govern <dir> given — say which markdown directories the ontology governs")
        cfg = default_config(root, wiki, roots, a.exclude or [])
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    proj = Project.load(root)
    if a.scan or not a.write:
        existing = proj.onto
        report = scan_project(proj)
        proj.onto = existing
        (root / REPORT_REL).write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        summary = {"report": REPORT_REL, "pages": report["pages"], "typed_pages": report["typed_pages"],
                   "types": {t: v["pages"] for t, v in report["types"].items()},
                   "controlled_fields": {k: {"declared_by": v["declared_by"], "outside": v["outside"]} for k, v in report["fields"].items()},
                   "conflicts": report["conflicts"], "scopes": {k: {"members": list(v["members"]), "observed": v["observed"]} for k, v in report["scopes"].items()},
                   "tags": len(report["tags"]), "relations": report["relations"], "unbound_candidates": [f"{c['type']}.{c['field']}" for c in report["unbound_candidates"]],
                   "links": report["links"]}
        print(json.dumps(summary, indent=1, ensure_ascii=False))
        if not a.write:
            return
    report_path = root / REPORT_REL
    if not report_path.exists():
        die(f"no init report at {REPORT_REL} — run `init --scan` first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    decisions = json.loads(Path(a.decisions).read_text(encoding="utf-8")) if a.decisions else {}
    existing = proj.onto if proj.ontology_path.exists() and not a.force else None
    if proj.ontology_path.exists() and proj.onto is None and not a.force:
        die(f"{proj.config['ontology_file']} exists but does not load ({proj.onto_error}); fix it or pass --force")
    data, added = build_ontology(report, decisions, a.by, existing)
    onto = save_ontology(proj, data)
    cls = classify_observed(report, onto)
    rendered = render_all(proj, templates=not a.no_templates)
    inst = {} if a.no_install else install(proj, skill_dir)
    viols, _pages = check_all(proj)
    s = summarize(viols)
    tc = term_counts(onto)
    append_log(proj, "project-ontology init — controlled vocabulary declared",
               f"{'Extended' if existing else 'Generated'} `{proj.config['ontology_file']}` from {report['pages']} pages: {tc['terms']} terms "
               f"({tc['approved']} approved, {tc['proposed']} proposed, {tc['deprecated']} deprecated). Observed values classified: "
               f"{cls['counts']} — unknown {len(cls['unknown'])}. Policy {onto.policy_default} (overrides {onto.overrides}), approval {onto.approval}. "
               f"Open violations: {s['violations']} (strict {s['strict']}, warn {s['warn']}) — pre-existing ones do not block (ratchet). "
               + ("Installed: PreToolUse/PostToolUse/Bash guard, SessionStart banner, CLAUDE.md block." if inst else ""))
    try:
        (root / STATE_REL).unlink()
    except OSError:
        pass
    print(json.dumps({"ontology": proj.config["ontology_file"], "added": added, "terms": tc, "classified": cls["counts"],
                      "unknown": cls["unknown"], "errors": onto.errors, "rendered": rendered, "install": inst,
                      "violations": s}, indent=1, ensure_ascii=False))
    if cls["unknown"]:
        sys.exit(1)


def cmd_install(a):
    root = find_root(Path(a.root)) if a.root else find_root()
    proj = Project.load(root)
    skill_dir = Path(a.skill_dir).resolve() if a.skill_dir else Path(__file__).resolve().parent.parent
    print(json.dumps(install(proj, skill_dir), indent=1))


def cmd_check(a):
    proj = _load(a)
    fmt = a.format
    if a.changed_since:
        try:
            # --relative / ls-files / `REF:./path` all speak paths relative to the project root, which matters
            # when the project is a subfolder of a larger repository; -z keeps names with spaces intact
            names = subprocess.run(["git", "diff", "--name-only", "-z", "--relative", a.changed_since, "--"], cwd=proj.root, capture_output=True, text=True, check=True).stdout.split("\0")
            names += subprocess.run(["git", "ls-files", "-z", "--others", "--exclude-standard"], cwd=proj.root, capture_output=True, text=True, check=True).stdout.split("\0")
            names = [n for n in names if n]
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            die(f"git failed: {e}")
        index = FileIndex(proj)
        fresh = []
        for rel in sorted(set(names)):
            if not proj.split_governed(rel) or not (proj.root / rel).exists():
                continue
            new = (proj.root / rel).read_text(encoding="utf-8", errors="replace")
            old = subprocess.run(["git", "show", f"{a.changed_since}:./{rel}"], cwd=proj.root, capture_output=True, text=True)
            before = check_text(proj, rel, old.stdout, index) if old.returncode == 0 else []
            had = Counter(_ratchet_key(v) for v in before)
            for v in check_text(proj, rel, new, index):
                k = _ratchet_key(v)
                if had[k] > 0:
                    had[k] -= 1
                elif v["policy"] == "strict" or a.include_warn:
                    fresh.append(v)
        print(format_violations(fresh, fmt) if fresh else ("[]" if fmt == "json" else f"ok — no new violations since {a.changed_since}"))
        sys.exit(1 if any(v["policy"] == "strict" for v in fresh) else 0)
    if a.all or not a.paths:
        viols, _ = check_all(proj)
    else:
        index = FileIndex(proj)
        viols = []
        for p in a.paths:
            rel = _cli_rel(proj, p)
            if rel is None or not proj.split_governed(rel):
                print(f"skip {p}: not a governed page", file=sys.stderr)
                continue
            viols += check_text(proj, rel, index.text(rel), index)
    if not a.include_warn and a.strict_only:
        viols = [v for v in viols if v["policy"] == "strict"]
    if fmt == "json":
        print(json.dumps({"summary": summarize(viols), "violations": json.loads(format_violations(viols, "json"))}, ensure_ascii=False, indent=1))
    else:
        print(format_violations(viols, fmt) if viols else "ok — no violations")
        s = summarize(viols)
        print(f"# {s['violations']} violation(s) on {s['pages']} page(s) — strict {s['strict']} · warn {s['warn']} · {s['by_rule']}", file=sys.stderr)
    sys.exit(1 if any(v["policy"] == "strict" for v in viols) else 0)


def cmd_hook(a):
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        sys.exit(0)
    root = Path(a.root or os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".").resolve()
    root = find_root(root)
    try:
        code, out = {"pre": hook_pre, "post": hook_post, "bash": hook_bash}[a.event](data, root)
    except Exception as e:  # a crashing hook must never silently disable enforcement, nor wedge the session
        code, out = (2, f"project-ontology hook error ({type(e).__name__}: {e}) — run `{ENGINE_CMD} check --all` to diagnose") if a.event == "pre" else (0, "")
    if out:
        print(out, file=sys.stderr if code == 2 else sys.stdout)
    sys.exit(code)


def cmd_propose(a):
    proj = _load(a)
    onto = proj.onto
    tid = a.id.strip()
    if not ID_RE.match(tid):
        die(f"`{tid}` is not a valid id — dot-joined segments of a-z, 0-9 and '-'")
    data = onto.data
    if tid in onto.terms:
        t = data[onto.terms[tid]["_section"]][tid]
        new_aliases = [x for x in (a.alias or []) if x not in as_list(t.get("aliases")) + as_list(t.get("proposed-aliases"))]
        if not new_aliases:
            die(f"`{tid}` is already registered (status {onto.terms[tid].get('status')})")
        t["proposed-aliases"] = as_list(t.get("proposed-aliases")) + new_aliases
        data["updated"] = today()
        save_ontology(proj, data)
        append_log(proj, f"ontology proposal — aliases for {tid}", f"Proposed aliases {new_aliases} for `{tid}` (by {actor()}). Awaiting human approval.")
        print(json.dumps({"id": tid, "proposed-aliases": new_aliases}))
        return
    kind = _kind_for_new_id(onto, tid, a.kind)
    if not a.definition:
        die("--definition is required: a term without a definition cannot be reviewed")
    section = SECTION_BY_KIND[kind]
    attrs = OrderedDict([("label", a.label or tid.split(".")[-1].replace("-", " ").capitalize())])
    if a.value:
        attrs["value"] = a.value
    attrs["definition"] = a.definition
    attrs["status"] = "proposed"
    if a.alias:
        attrs["proposed-aliases"] = a.alias
    if kind == "relation":
        attrs["domain"] = [x.strip() for x in (a.domain or "").split(",") if x.strip()]
        attrs["range"] = [x.strip() for x in (a.range or "").split(",") if x.strip()]
    attrs["since"] = today()
    if a.source:
        attrs["source"] = a.source
    attrs["proposed-by"] = actor()
    if kind == "vocab":
        tp, fld, _ = tid.split(".")
        bkey = f"{tp}.{fld}"
        if bkey not in onto.fields and binding_key("*", fld) not in onto.fields:
            if not a.bind:
                die(f"`{tp}.{fld}` is not a controlled field yet. Proposing `{tid}` would put every `{fld}:` value on {tp} "
                    f"pages under control — pass --bind if that is intended.")
            data["fields"][bkey] = OrderedDict([("kind", "vocab")])
    if kind == "entity" and a.bind_field:
        data["fields"][binding_key("*", a.bind_field)] = OrderedDict([("kind", "entity"), ("namespace", tid.split(".")[0])])
    # keep siblings together: after the last sibling by default, or exactly where --before / --after says —
    # a vocabulary's order is its ranking (critical|high|medium|low), so "urgent" belongs above "critical"
    sec = data[section]
    items = list(sec.items())
    parent = tid.rsplit(".", 1)[0]
    anchor = a.before or a.after
    if anchor:
        if anchor not in sec:
            die(f"--{'before' if a.before else 'after'} `{anchor}` is not a declared {kind} term")
        if anchor.rsplit(".", 1)[0] != parent:
            die(f"`{anchor}` is not a sibling of `{tid}` (different parent) — order only matters among siblings")
        at = next(i for i, (k, _) in enumerate(items) if k == anchor) + (0 if a.before else 1)
        items.insert(at, (tid, attrs))
    else:
        at = max((i for i, (k, _) in enumerate(items) if k.rsplit(".", 1)[0] == parent), default=len(items) - 1)
        items.insert(at + 1, (tid, attrs))
    data[section] = OrderedDict(items)
    data["updated"] = today()
    new = save_ontology(proj, data)
    if new.errors and any(tid in e for e in new.errors):
        print("warning: " + "; ".join(e for e in new.errors if tid in e), file=sys.stderr)
    append_log(proj, f"ontology proposal — {tid}", f"Proposed `{tid}` ({kind}) — {a.definition} (by {actor()}"
               + (f", needed by {a.source}" if a.source else "") + "). Usable now; awaiting human approval (/ontology:approve).")
    print(json.dumps({"id": tid, "kind": kind, "status": "proposed", "file": proj.config["ontology_file"]}))


def cmd_approve(a):
    proj = _load(a)
    if not a.by:
        die("--by <human name> is required: approval is a human gate, and the record says who approved")
    data, onto = proj.onto.data, proj.onto
    done, skipped = [], []
    ids = []
    for pat in a.ids:
        m = [tid for tid in onto.terms if fnmatch.fnmatchcase(tid, pat)]
        if not m:
            die(f"no term matches `{pat}`")
        ids += m
    for tid in dict.fromkeys(ids):
        t = data[onto.terms[tid]["_section"]][tid]
        if t.get("status") == "deprecated":
            skipped.append(f"{tid} (deprecated)")
            continue
        changed = False
        if t.get("status") != "approved" and not a.aliases_only:
            t["status"], t["approved-by"], t["approved-on"] = "approved", a.by, today()
            changed = True
        if t.get("proposed-aliases"):
            t["aliases"] = as_list(t.get("aliases")) + as_list(t.pop("proposed-aliases"))
            changed = True
        (done if changed else skipped).append(tid)
    if done:
        data["updated"] = today()
        save_ontology(proj, data)
        append_log(proj, f"ontology approval — {len(done)} term(s)", f"Approved by {a.by}: " + ", ".join(f"`{x}`" for x in done))
    print(json.dumps({"approved": done, "skipped": skipped}, indent=1))


def cmd_deprecate(a):
    proj = _load(a)
    if not a.by:
        die("--by <human name> is required: deprecation is a human gate")
    data, onto = proj.onto.data, proj.onto
    if a.id not in onto.terms:
        die(f"no term `{a.id}`")
    t = data[onto.terms[a.id]["_section"]][a.id]
    if a.replaced_by:
        r = onto.terms.get(a.replaced_by)
        if not r:
            die(f"replacement `{a.replaced_by}` is not a declared term")
        if r["_kind"] != onto.terms[a.id]["_kind"] or (r["_kind"] in ("vocab", "entity") and term_parent(r) != term_parent(onto.terms[a.id])):
            die(f"`{a.replaced_by}` cannot replace `{a.id}`: it must be the same kind of term under the same parent")
        if r.get("status") == "deprecated":
            die(f"`{a.replaced_by}` is itself deprecated")
        t["replaced-by"] = a.replaced_by
    t["status"], t["deprecated-by"], t["deprecated-on"] = "deprecated", a.by, today()
    if a.reason:
        t["reason"] = a.reason
    data["updated"] = today()
    save_ontology(proj, data)
    append_log(proj, f"ontology deprecation — {a.id}", f"Deprecated `{a.id}` by {a.by}" + (f", replaced by `{a.replaced_by}`" if a.replaced_by else "")
               + (f": {a.reason}" if a.reason else "") + ". Pages using it are flagged; `/ontology:apply` rewrites them when a replacement exists.")
    print(json.dumps({"deprecated": a.id, "replaced-by": a.replaced_by}))


def cmd_apply(a):
    proj = _load(a)
    index = FileIndex(proj)
    rels = []
    if a.paths:
        for p in a.paths:
            rel = _cli_rel(proj, p)
            if rel and proj.split_governed(rel):
                rels.append(rel)
    else:
        rels = list(proj.iter_governed())
    total, files = 0, 0
    for rel in rels:
        text = index.text(rel)
        edits = plan_rewrites(proj, rel, text, index)
        if not edits:
            continue
        new = apply_rewrites(text, edits)
        if new == text:
            continue
        files += 1
        total += len(edits)
        for e in edits:
            old = e.get("old")
            print(f"{'would rewrite' if a.dry_run else 'rewrote'} {rel}:{e.get('line') or '-'} {e['rule']} {old} → {e['new']}")
        if not a.dry_run:
            (proj.root / rel).write_text(new, encoding="utf-8")
    if a.dry_run:
        print(f"# dry run: {total} rewrite(s) in {files} file(s); nothing written")
        return
    viols, _ = check_all(proj)
    s = summarize(viols)
    if total:
        append_log(proj, "ontology apply — canonical values", f"Rewrote {total} value(s)/link(s) in {files} page(s) to canonical terms. "
                   f"Remaining violations: {s['violations']} (strict {s['strict']}, warn {s['warn']}) — these need a human decision.")
    print(f"# applied {total} rewrite(s) in {files} file(s) · remaining violations {s['violations']} (strict {s['strict']} · warn {s['warn']})")


def cmd_render(a):
    proj = _load(a)
    print(json.dumps(render_all(proj, templates=a.templates), indent=1))


def cmd_status(a):
    proj = Project.load(find_root(Path(a.root)) if a.root else find_root(), require=not a.banner)
    if proj is None:
        return
    if proj.onto is None:
        msg = f"🧭 project-ontology: ontology not loaded — {proj.onto_error}. Writes to governed pages are blocked until it is fixed."
        print(msg if a.banner else json.dumps({"error": proj.onto_error}))
        return
    onto = proj.onto
    viols, pages = cached_check(proj)
    s, tc = summarize(viols), term_counts(onto)
    pending = [t["_id"] for t in onto.terms.values() if t.get("status") == "proposed"]
    palias = [t["_id"] for t in onto.terms.values() if t.get("proposed-aliases")]
    settings = proj.root / ".claude/settings.json"
    hooked = settings.exists() and "ontology-guard.sh" in settings.read_text(encoding="utf-8")
    if a.banner:
        ov = ", ".join(f"{k}: {v}" for k, v in onto.overrides.items())
        print(f"🧭 project-ontology [{proj.config['ontology_file']}]: {tc['terms']} terms ({tc['approved']} approved · {tc['proposed']} proposed · "
              f"{tc['deprecated']} deprecated) · policy {onto.policy_default}{f' ({ov})' if ov else ''} · approval {onto.approval}"
              + ("" if hooked else " · ⚠ write hook NOT installed"))
        print(f"  open violations: {s['violations']} on {s['pages']} page(s) (strict {s['strict']} · warn {s['warn']}) — pre-existing ones do not block; new ones do"
              + (f" · {len(pending)} proposed term(s) and {len(palias)} alias set(s) await human approval" if pending or palias else ""))
        print(f"  before writing frontmatter or [[links]]: {proj.config.get('doc_file')} · new value → {ENGINE_CMD} propose … · check: {ENGINE_CMD} check <file>")
        if onto.errors:
            print(f"  ⚠ {len(onto.errors)} ontology error(s): {onto.errors[0]}")
        return
    info = {"file": proj.config["ontology_file"], "doc": proj.config.get("doc_file"), "engine": ENGINE_VERSION, "hook_installed": hooked,
            "policy": {"default": onto.policy_default, "proposed": onto.policy_proposed, "overrides": onto.overrides, "approval": onto.approval},
            "terms": tc, "violations": s, "pending_approval": pending[:50], "pending_aliases": palias[:50], "pages": len(pages), "errors": onto.errors}
    print(json.dumps(info, indent=1, ensure_ascii=False))


def cmd_ls(a):
    proj = _load(a)
    rows = []
    for t in proj.onto.terms.values():
        if a.prefix and not t["_id"].startswith(a.prefix):
            continue
        if a.status and t.get("status") != a.status:
            continue
        if a.kind and t["_kind"] != a.kind:
            continue
        rows.append((t["_id"], t["_kind"], t.get("status"), term_value(t) if t["_kind"] != "relation" else "", t.get("label") or ""))
    for r in rows[: a.limit]:
        print("\t".join(str(x) for x in r))
    print(f"# {len(rows)} term(s)", file=sys.stderr)


def main(argv=None):
    p = argparse.ArgumentParser(prog="ontology.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="mine the vault (--scan) and/or write the ontology (--write)")
    s.add_argument("--root", default=".")
    s.add_argument("--skill-dir")
    s.add_argument("--scan", action="store_true", help="write the init report (default when --write is absent)")
    s.add_argument("--write", action="store_true", help="build ontology.yaml from the report + decisions, render, install")
    s.add_argument("--decisions", help="JSON file with interview decisions (see references/init-interview.md)")
    s.add_argument("--by", help="who made the interview decisions (recorded as approved-by)")
    s.add_argument("--wiki-root", help="wiki directory (auto-detected: wiki, .claude/wiki, docs/wiki)")
    s.add_argument("--no-wiki", action="store_true")
    s.add_argument("--govern", action="append", help="markdown directory to govern (no-wiki projects)")
    s.add_argument("--exclude", action="append", help="glob relative to a governed root to skip")
    s.add_argument("--force", action="store_true", help="rebuild ontology.yaml from scratch instead of extending it")
    s.add_argument("--force-config", action="store_true", help="rewrite .claude/ontology/config.json")
    s.add_argument("--no-install", action="store_true", help="do not install hooks / CLAUDE.md block")
    s.add_argument("--no-templates", action="store_true", help="do not sync binding comments into page templates")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("install", help="vendor engine + hooks, merge settings.json, CLAUDE.md block")
    s.add_argument("--root")
    s.add_argument("--skill-dir")
    s.set_defaults(fn=cmd_install)

    s = sub.add_parser("check", help="rules for files, the vault, or changes since a git ref")
    s.add_argument("paths", nargs="*")
    s.add_argument("--root")
    s.add_argument("--all", action="store_true")
    s.add_argument("--changed-since", metavar="REF", help="CI ratchet: only violations new relative to REF")
    s.add_argument("--format", choices=["text", "json", "lint"], default="text")
    s.add_argument("--strict-only", action="store_true", help="hide warn-level violations")
    s.add_argument("--include-warn", action="store_true", help="with --changed-since: report new warn violations too")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("hook", help="Claude Code hook entry point (JSON on stdin)")
    s.add_argument("event", choices=["pre", "post", "bash"])
    s.add_argument("--root")
    s.set_defaults(fn=cmd_hook)

    s = sub.add_parser("propose", help="register a new term (status: proposed)")
    s.add_argument("id")
    s.add_argument("--root")
    s.add_argument("--label")
    s.add_argument("--definition")
    s.add_argument("--value", help="exact spelling on pages when it differs from the id leaf (P1, 🟡)")
    s.add_argument("--alias", action="append", help="alternative spelling (proposed alias); on an existing term adds aliases")
    s.add_argument("--kind", choices=["type", "vocab", "entity", "tag", "relation"])
    s.add_argument("--domain", help="relation: comma-separated source page types")
    s.add_argument("--range", help="relation: comma-separated target page types")
    s.add_argument("--bind", action="store_true", help="vocab: make <type>.<field> a controlled field if it is not one yet")
    s.add_argument("--bind-field", help="entity: bind this frontmatter field (all types) to the entity namespace")
    s.add_argument("--source", help="page or context that needs the term")
    order = s.add_mutually_exclusive_group()
    order.add_argument("--before", metavar="ID", help="insert before this sibling (vocabulary order is ranking)")
    order.add_argument("--after", metavar="ID", help="insert after this sibling")
    s.set_defaults(fn=cmd_propose)

    s = sub.add_parser("approve", help="proposed → approved (human gate)")
    s.add_argument("ids", nargs="+", help="term ids (globs allowed: 'tag.*')")
    s.add_argument("--by", help="the human approving")
    s.add_argument("--aliases-only", action="store_true", help="approve proposed aliases, leave term status")
    s.add_argument("--root")
    s.set_defaults(fn=cmd_approve)

    s = sub.add_parser("deprecate", help="retire a term (human gate)")
    s.add_argument("id")
    s.add_argument("--replaced-by")
    s.add_argument("--reason")
    s.add_argument("--by")
    s.add_argument("--root")
    s.set_defaults(fn=cmd_deprecate)

    s = sub.add_parser("apply", help="rewrite mechanical cases to canonical terms")
    s.add_argument("paths", nargs="*")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--root")
    s.set_defaults(fn=cmd_apply)

    s = sub.add_parser("render", help="ONTOLOGY.md (+ --templates)")
    s.add_argument("--templates", action="store_true")
    s.add_argument("--root")
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("status", help="counts, policy, open violations")
    s.add_argument("--banner", action="store_true")
    s.add_argument("--root")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("ls", help="list terms")
    s.add_argument("--prefix")
    s.add_argument("--status", choices=list(STATUSES))
    s.add_argument("--kind", choices=["type", "vocab", "entity", "tag", "relation"])
    s.add_argument("--limit", type=int, default=500)
    s.add_argument("--root")
    s.set_defaults(fn=cmd_ls)

    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
