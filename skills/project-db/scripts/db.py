#!/usr/bin/env python3
"""project-db engine — build, sync, query, and publish a project's queryable SQLite database.

Vendored into <project>/.claude/db/db.py by the project-db skill (/db:init). Standard library only,
so it runs anywhere python3 runs. One file on purpose: the SessionStart hook, the CLI, the local MCP
server, and the D1 publisher all import the same guardrails from here.

Subcommands
  init        write config, vendor engine + templates into .claude/db, install hook/mandate, build
  install     (re)vendor templates + merge CLAUDE.md block, settings hook, .mcp.json, .gitignore
  build       full rebuild (drop + reload)
  sync        incremental sync (content-hash per file); --quiet prints only when something changed
  query       run ONE read-only statement with timeout, row cap, cell truncation, CSV output, audit
  schema      print the agent-facing schema summary (also written to .claude/db/SCHEMA.md on sync)
  search      full-text search over pages (and raw documents)
  status      freshness, counts, mode, last sync / publish
  audit       show recent queries from the audit log (the feedback loop for new views)
  export-d1   write a D1-safe SQL import file (no BEGIN/COMMIT, statements < 100 KB, FTS rebuilt)
  verify      integrity checks: counts match files, views compile, FTS works, read-only enforced

Ontology: when the project-ontology skill is installed (.claude/ontology/ontology.py), every sync loads
its terms, aliases, field bindings, derived page ids and violations into ontology_* tables by importing
that engine — one rule implementation shared with the write hook, so the two can never disagree.
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ENGINE_VERSION = "1.1.0"
SCHEMA_VERSION = 2  # 2: pages.ontology_id + ontology_terms / ontology_aliases / ontology_fields / ontology_violations
ONTOLOGY_ENGINE_REL = ".claude/ontology/ontology.py"
ONTOLOGY_API = 1
DB_DIR_REL = ".claude/db"
CONFIG_REL = f"{DB_DIR_REL}/config.json"
SENTINEL_OPEN = "<!-- project-db:managed -->"
SENTINEL_CLOSE = "<!-- /project-db:managed -->"
HOOK_REL = ".claude/hooks/db-context.sh"

BASE_KEYS = {"type", "client", "status", "created", "updated", "title"}
MULTI_KEYS = {"tags", "sources"}  # loaded into their own tables; kept in frontmatter JSON too
PLURALS = {"entity": "entities", "gap": "gaps", "index": "indexes", "person": "people", "process": "processes"}


# ----------------------------------------------------------------------------- helpers

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_root(start: Path | None = None) -> Path:
    """Walk up from cwd to the directory holding .claude/db/config.json; fall back to cwd."""
    p = (start or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / CONFIG_REL).exists():
            return cand
    return p


def load_config(root: Path) -> dict:
    cfg_path = root / CONFIG_REL
    if not cfg_path.exists():
        die(f"no project-db config at {cfg_path} — run /db:init first")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def save_config(root: Path, cfg: dict) -> None:
    cfg_path = root / CONFIG_REL
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def die(msg: str, code: int = 2) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def plural(word: str) -> str:
    if word in PLURALS:
        return PLURALS[word]
    if word.endswith("y") and word[-2:-1] not in "aeiou":
        return word[:-1] + "ies"
    if word.endswith(("s", "x", "ch", "sh")):
        return word + "es"
    return word + "s"


def ident(name: str) -> str:
    """Make a safe SQL identifier out of a frontmatter key or CSV header."""
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip()).strip("_").lower()
    if not s:
        s = "col"
    if s[0].isdigit():
        s = "c_" + s
    if s in {"select", "from", "where", "order", "group", "table", "index", "default", "values", "key"}:
        s += "_"
    return s


def sql_str(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, bytes):
        return "X'" + v.hex() + "'"
    return "'" + str(v).replace("'", "''") + "'"


# ----------------------------------------------------------------------------- frontmatter parsing

FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")


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
        # split on commas not inside [[...]] or quotes
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


def parse_yaml_subset(fm_text: str) -> tuple[dict, dict]:
    """Parse the YAML subset wiki frontmatter uses. Returns (data, docs) where docs maps a key to
    the trailing `# comment` on its line (templates use these as value hints → column docs).

    Deliberately never PyYAML: with PyYAML installed `related: [[Page]]` parses as a nested list and its
    link disappears, so the same wiki would index differently on two machines. project-ontology's
    engine uses this exact parser (its test suite pins the parity). Block lists may be indented or
    written at the key's own indent (`tags:` then `- a`), both valid YAML."""
    data: dict = {}
    docs: dict = {}
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z0-9_\-]+):(.*)$", line)
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


_CODE_FENCE_RE = re.compile(r"^[ \t]*(```|~~~)[^\n]*\n.*?^[ \t]*\1[ \t]*$", re.M | re.S)
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def visible_body(body: str) -> str:
    """What a reader sees as prose: HTML comments (template guidance Obsidian never renders), fenced
    code and inline code blanked out — links inside them are not links. Newlines are kept so line
    context stays true."""
    body = re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), body, flags=re.S)
    body = _CODE_FENCE_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), body)
    return _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), body)


def parse_page(text: str, relpath: str) -> dict:
    fm_text, body = split_frontmatter(text)
    fm, _docs = parse_yaml_subset(fm_text) if fm_text is not None else ({}, {})
    if not isinstance(fm, dict):
        fm = {}
    slug = Path(relpath).stem
    title = None
    for line in body.splitlines():
        m = HEADING_RE.match(line.strip())
        if m and len(m.group(1)) == 1:
            title = m.group(2).strip()
            break
    if not title:
        t = fm.get("title")
        title = str(t) if t else slug
    # sections
    sections, cur_head, cur_level, buf, ord_ = [], "", 0, [], 0
    for line in body.splitlines():
        m = HEADING_RE.match(line.strip()) if line.startswith("#") else None
        if m:
            content = "\n".join(buf).strip()
            if content or cur_head:
                sections.append((ord_, cur_level, cur_head, content))
                ord_ += 1
            cur_head, cur_level, buf = m.group(2).strip(), len(m.group(1)), []
        else:
            buf.append(line)
    content = "\n".join(buf).strip()
    if content or cur_head:
        sections.append((ord_, cur_level, cur_head, content))
    # links: body + frontmatter string values. HTML comments are template guidance ("<!-- link to
    # [[feature|Features]] -->") and code is code — Obsidian renders neither as a link.
    links = []
    visible = visible_body(body)
    for line in visible.splitlines():
        for m in WIKILINK_RE.finditer(line):
            links.append((m.group(1).strip(), (m.group(2) or "").strip(), "body", line.strip()[:200]))

    def walk(v, key):
        if isinstance(v, str):
            for m in WIKILINK_RE.finditer(v):
                links.append((m.group(1).strip(), (m.group(2) or "").strip(), f"frontmatter:{key}", v[:200]))
        elif isinstance(v, list):
            for x in v:
                walk(x, key)
        elif isinstance(v, dict):
            for k, x in v.items():
                walk(x, f"{key}.{k}")

    for k, v in fm.items():
        walk(v, k)
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    sources = fm.get("sources") or []
    if isinstance(sources, str):
        sources = [sources]
    sources = [str(s).strip() for s in sources if s is not None and str(s).strip()]
    words = len(re.findall(r"\w+", body))
    return {
        "slug": slug, "title": title, "fm": fm, "body": body, "sections": sections,
        "links": links, "tags": [str(t) for t in tags], "sources": sources, "word_count": words,
    }


# ----------------------------------------------------------------------------- schema

BASE_DDL = [
    """CREATE TABLE IF NOT EXISTS pages (
  id INTEGER PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL,
  ontology_id TEXT,
  collection TEXT NOT NULL,
  type TEXT,
  title TEXT NOT NULL,
  scope TEXT,
  status TEXT,
  created TEXT,
  updated TEXT,
  frontmatter TEXT NOT NULL DEFAULT '{}',
  body TEXT NOT NULL DEFAULT '',
  word_count INTEGER NOT NULL DEFAULT 0,
  content_hash TEXT NOT NULL,
  mtime REAL,
  indexed_at TEXT NOT NULL
)""",
    "CREATE INDEX IF NOT EXISTS pages_slug_idx ON pages(slug)",
    "CREATE INDEX IF NOT EXISTS pages_ontology_idx ON pages(ontology_id)",
    "CREATE INDEX IF NOT EXISTS pages_type_idx ON pages(type, scope, status)",
    """CREATE TABLE IF NOT EXISTS page_fields (
  page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  key TEXT NOT NULL,
  value TEXT,
  ord INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (page_id, key, ord)
)""",
    "CREATE INDEX IF NOT EXISTS page_fields_kv_idx ON page_fields(key, value)",
    """CREATE TABLE IF NOT EXISTS links (
  id INTEGER PRIMARY KEY,
  from_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  to_slug TEXT NOT NULL,
  to_id INTEGER,
  label TEXT,
  kind TEXT NOT NULL DEFAULT 'body',
  context TEXT,
  ambiguous INTEGER NOT NULL DEFAULT 0,
  match TEXT
)""",
    "CREATE INDEX IF NOT EXISTS links_from_idx ON links(from_id)",
    "CREATE INDEX IF NOT EXISTS links_to_idx ON links(to_id)",
    "CREATE INDEX IF NOT EXISTS links_to_slug_idx ON links(to_slug)",
    """CREATE TABLE IF NOT EXISTS tags (
  page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  tag TEXT NOT NULL,
  PRIMARY KEY (page_id, tag)
)""",
    "CREATE INDEX IF NOT EXISTS tags_tag_idx ON tags(tag)",
    """CREATE TABLE IF NOT EXISTS sources (
  page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  source_path TEXT NOT NULL,
  raw_id INTEGER,
  PRIMARY KEY (page_id, source_path)
)""",
    """CREATE TABLE IF NOT EXISTS sections (
  page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  ord INTEGER NOT NULL,
  level INTEGER NOT NULL,
  heading TEXT NOT NULL,
  content TEXT NOT NULL,
  word_count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (page_id, ord)
)""",
    """CREATE TABLE IF NOT EXISTS raw_documents (
  id INTEGER PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL DEFAULT '',
  bytes INTEGER NOT NULL DEFAULT 0,
  content_hash TEXT NOT NULL,
  indexed_at TEXT NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS log_entries (
  ord INTEGER PRIMARY KEY,
  date TEXT,
  title TEXT NOT NULL,
  body TEXT NOT NULL DEFAULT ''
)""",
    """CREATE TABLE IF NOT EXISTS column_docs (
  object TEXT NOT NULL,
  column TEXT NOT NULL,
  doc TEXT NOT NULL,
  PRIMARY KEY (object, column)
)""",
    """CREATE TABLE IF NOT EXISTS sync_state (
  key TEXT PRIMARY KEY,
  value TEXT
)""",
    """CREATE TABLE IF NOT EXISTS ontology_terms (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  namespace TEXT NOT NULL,
  parent TEXT,
  value TEXT,
  label TEXT,
  definition TEXT,
  status TEXT NOT NULL,
  replaced_by TEXT,
  since TEXT,
  approved_by TEXT,
  approved_on TEXT,
  source TEXT,
  domain TEXT,
  range TEXT
)""",
    "CREATE INDEX IF NOT EXISTS ontology_terms_parent_idx ON ontology_terms(parent, status)",
    """CREATE TABLE IF NOT EXISTS ontology_aliases (
  alias TEXT NOT NULL,
  term_id TEXT NOT NULL,
  status TEXT NOT NULL,
  PRIMARY KEY (alias, term_id)
)""",
    """CREATE TABLE IF NOT EXISTS ontology_fields (
  binding TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  field TEXT NOT NULL,
  kind TEXT NOT NULL,
  namespace TEXT,
  relation TEXT
)""",
    """CREATE TABLE IF NOT EXISTS ontology_violations (
  id INTEGER PRIMARY KEY,
  page_id INTEGER,
  path TEXT NOT NULL,
  line INTEGER,
  rule TEXT NOT NULL,
  policy TEXT NOT NULL,
  family TEXT,
  field TEXT,
  value TEXT,
  message TEXT NOT NULL,
  suggestion TEXT,
  nearest TEXT
)""",
    "CREATE INDEX IF NOT EXISTS ontology_violations_page_idx ON ontology_violations(page_id)",
]

BASE_COLUMN_DOCS = {
    "pages": {
        "_": "One row per markdown page. The wiki page is the record; this row is its index.",
        "path": "file path relative to the collection root (unique)",
        "slug": "filename stem — the [[wikilink]] target",
        "ontology_id": "dot-notated id derived by project-ontology from the path (client.acme.gap.co-op-billing); NULL without an ontology",
        "collection": "which configured collection loaded it (e.g. wiki)",
        "type": "frontmatter `type` — one typed view exists per distinct value",
        "title": "first H1, else frontmatter title, else slug",
        "scope": "frontmatter scope field (usually `client`); typed views alias it as `client`",
        "status": "frontmatter `status` (meaning depends on type — see the typed view)",
        "frontmatter": "full frontmatter as JSON: json_extract(frontmatter, '$.some-key')",
        "body": "markdown body without frontmatter (truncated in query output; use sections for parts)",
        "content_hash": "sha256 of the file; drives incremental sync",
    },
    "page_fields": {
        "_": "Every frontmatter key flattened to rows (lists → one row per item). Filter on ANY field.",
        "key": "frontmatter key as written (e.g. resolution-approach)",
        "value": "scalar value as text; NULL when the key is empty",
        "ord": "position inside a list value, 0 for scalars",
    },
    "links": {
        "_": "[[wikilinks]] found in bodies and frontmatter. to_id is NULL when the target page does not exist.",
        "to_slug": "link target as written",
        "to_id": "resolved pages.id, NULL if broken or ambiguous",
        "kind": "'body' or 'frontmatter:<key>'",
        "context": "the line the link appeared on",
        "ambiguous": "1 when several pages share the target slug",
        "match": "how the target resolved: slug (exact), title, fuzzy (slugified), label ([[type|slug]] vaults), folder (dir with overview/README) — anything but slug is worth fixing in the source",
    },
    "tags": {"_": "frontmatter tags, one row per tag", "tag": "tag text"},
    "sources": {"_": "frontmatter sources (raw documents a page cites)", "raw_id": "raw_documents.id when the file was found and loaded"},
    "sections": {"_": "page bodies split by heading, in order — query one section instead of the whole body", "heading": "heading text without #", "level": "1-6 (0 = text before the first heading)"},
    "raw_documents": {"_": "raw sources cited by pages (transcripts, analyses, exports), full text", "kind": "file extension without dot", "path": "path relative to project root"},
    "log_entries": {"_": "entries parsed from the wiki operation log (_log.md), newest last", "date": "YYYY-MM-DD parsed from the heading"},
    "column_docs": {"_": "this documentation, queryable", "object": "table or view name"},
    "sync_state": {"_": "engine bookkeeping: last_sync, counts, mode"},
    "ontology_terms": {"_": "project-ontology terms (wiki/_schema/ontology.yaml): the legal values of every controlled field, with lifecycle status",
                       "id": "dot-notated term id: <type>.<field>.<value> (vocabulary), <namespace>.<slug> (entity), tag.<path>, rel.<name>, type.<name>",
                       "kind": "type | vocab | entity | tag | relation", "parent": "the id minus its last segment — vocabulary terms share parent <type>.<field>",
                       "value": "the exact spelling pages must use", "status": "proposed | approved | deprecated",
                       "replaced_by": "for deprecated terms: the term to use instead"},
    "ontology_aliases": {"_": "alternative spellings mapped to a term (search expands them; the write hook flags them)", "status": "approved | proposed"},
    "ontology_fields": {"_": "which frontmatter fields are controlled, and by what kind of term", "binding": "<type>.<field>, or *.<field> for every type",
                        "namespace": "entity bindings: the entity namespace (e.g. client)", "relation": "relation bindings: the rel.* term (domain/range in ontology_terms)"},
    "ontology_violations": {"_": "every current ontology violation, from the same rules the PreToolUse write hook runs; refreshed on every sync",
                            "rule": "value-unknown · value-noncanonical · value-deprecated · value-proposed · type-unknown · link-broken · link-ambiguous · link-noncanonical · relation-broken · relation-range · id-duplicate",
                            "policy": "strict (a write adding it is blocked) | warn", "path": "pages.path when the page is in a collection, else the project-relative path",
                            "suggestion": "what to write instead (approved values, canonical link)", "nearest": "closest approved values, comma-separated"},
}


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    for ddl in BASE_DDL:
        conn.execute(ddl)
    if fts_available(conn):
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(title, body, content='pages', content_rowid='id')")
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS raw_fts USING fts5(title, body, content='raw_documents', content_rowid='id')")
    for obj, cols in BASE_COLUMN_DOCS.items():
        for col, doc in cols.items():
            conn.execute("INSERT OR REPLACE INTO column_docs(object, column, doc) VALUES (?,?,?)", (obj, col, doc))


_FTS_AVAILABLE: bool | None = None


def fts_available(conn: sqlite3.Connection | None = None) -> bool:
    """FTS5 is a property of the linked SQLite library, not of a database — probe once on :memory:
    so the guarded read-only connection (which denies PRAGMA) never has to ask."""
    global _FTS_AVAILABLE
    if _FTS_AVAILABLE is None:
        probe = sqlite3.connect(":memory:")
        try:
            probe.execute("CREATE VIRTUAL TABLE t USING fts5(a)")
            _FTS_AVAILABLE = True
        except sqlite3.OperationalError:
            _FTS_AVAILABLE = False
        finally:
            probe.close()
    return _FTS_AVAILABLE


def set_state(conn, key, value) -> None:
    conn.execute("INSERT OR REPLACE INTO sync_state(key, value) VALUES (?,?)", (key, json.dumps(value) if not isinstance(value, str) else value))


def get_state(conn, key, default=None):
    row = conn.execute("SELECT value FROM sync_state WHERE key=?", (key,)).fetchone()
    return row[0] if row else default


# ----------------------------------------------------------------------------- loading

def iter_collection_files(root: Path, coll: dict):
    croot = root / coll.get("root", ".")
    if not croot.exists():
        return
    pattern = coll.get("glob", "**/*.md")
    excludes = coll.get("exclude", [])
    for p in sorted(croot.glob(pattern)):
        if not p.is_file():
            continue
        rel = p.relative_to(croot).as_posix()
        if any(part.startswith(".") for part in Path(rel).parts):
            continue
        # fnmatch: '*' crosses '/', so "_schema/*" excludes the whole _schema tree (schema docs are
        # about the content, not content — their example [[links]] would all count as broken)
        if any(fnmatch.fnmatch(rel, ex) for ex in excludes):
            continue
        yield p, rel


def upsert_page(conn, coll: dict, rel: str, text: str, chash: str, mtime: float, exclude_keys: set) -> int:
    parsed = parse_page(text, rel)
    fm = {k: v for k, v in parsed["fm"].items() if k not in exclude_keys}
    type_field = coll.get("type_field", "type")
    scope_field = coll.get("scope_field", "client")
    ptype = fm.get(type_field) or coll.get("default_type")
    if isinstance(ptype, str):
        ptype = ptype.strip().lower()
        if "|" in ptype:  # template placeholders like "feature|entity|..." are not real types
            ptype = None
    else:
        ptype = coll.get("default_type")
    scope = fm.get(scope_field)
    row = conn.execute("SELECT id FROM pages WHERE path=?", (rel,)).fetchone()
    vals = (
        parsed["slug"], coll["name"], ptype, parsed["title"], str(scope) if scope is not None else None,
        str(fm.get("status")) if fm.get("status") is not None else None,
        str(fm.get("created")) if fm.get("created") is not None else None,
        str(fm.get("updated")) if fm.get("updated") is not None else None,
        json.dumps(fm, ensure_ascii=False, default=str), parsed["body"], parsed["word_count"], chash, mtime, now_iso(),
    )
    if row:
        pid = row[0]
        conn.execute(
            "UPDATE pages SET slug=?, collection=?, type=?, title=?, scope=?, status=?, created=?, updated=?, frontmatter=?, body=?, word_count=?, content_hash=?, mtime=?, indexed_at=? WHERE id=?",
            vals + (pid,))
        for t in ("page_fields", "links", "tags", "sources", "sections"):
            conn.execute(f"DELETE FROM {t} WHERE {'from_id' if t == 'links' else 'page_id'}=?", (pid,))
    else:
        cur = conn.execute(
            "INSERT INTO pages(slug, collection, type, title, scope, status, created, updated, frontmatter, body, word_count, content_hash, mtime, indexed_at, path) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            vals + (rel,))
        pid = cur.lastrowid
    for k, v in fm.items():
        items = v if isinstance(v, list) else [v]
        for i, item in enumerate(items):
            if isinstance(item, (dict, list)):
                item = json.dumps(item, ensure_ascii=False, default=str)
            conn.execute("INSERT OR REPLACE INTO page_fields(page_id, key, value, ord) VALUES (?,?,?,?)",
                         (pid, k, None if item is None else str(item), i))
    for to_slug, label, kind, context in parsed["links"]:
        conn.execute("INSERT INTO links(from_id, to_slug, label, kind, context) VALUES (?,?,?,?,?)",
                     (pid, to_slug, label or None, kind, context))
    for t in dict.fromkeys(parsed["tags"]):
        conn.execute("INSERT OR IGNORE INTO tags(page_id, tag) VALUES (?,?)", (pid, t))
    for s in dict.fromkeys(parsed["sources"]):
        conn.execute("INSERT OR IGNORE INTO sources(page_id, source_path) VALUES (?,?)", (pid, s))
    for ord_, level, heading, content in parsed["sections"]:
        conn.execute("INSERT INTO sections(page_id, ord, level, heading, content, word_count) VALUES (?,?,?,?,?,?)",
                     (pid, ord_, level, heading, content, len(re.findall(r"\w+", content))))
    return pid


def slugify(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.strip().lower())).strip("-")


def resolve_links(conn) -> None:
    """Resolve [[targets]] the way a reader would: exact slug or path first (what Obsidian does), then
    the page whose title matches, then the slugified target ("Budget Management" → budget-management),
    then the LABEL when the target is a type word — some vaults write [[gap|budget-engine]] meaning
    "the gap page budget-engine" — and finally a folder note (a directory named like the target with
    an overview/README/index page). `match` records which rule fired so a lint can treat anything but
    'slug' as 'please fix the link in the source'."""
    by_slug: dict[str, list[tuple[int, str | None]]] = {}
    by_title: dict[str, list[tuple[int, str | None]]] = {}
    by_folder: dict[str, list[tuple[int, str | None]]] = {}
    scope_of: dict[int, str | None] = {}
    types = {r[0] for r in conn.execute("SELECT DISTINCT lower(type) FROM pages WHERE type IS NOT NULL")}
    for pid, slug, scope, path, title in conn.execute("SELECT id, slug, scope, path, title FROM pages"):
        scope_of[pid] = scope
        by_slug.setdefault(slug.lower(), []).append((pid, scope))
        stem_path = path[:-3] if path.endswith(".md") else path
        by_slug.setdefault(stem_path.lower(), []).append((pid, scope))
        by_title.setdefault(title.strip().lower(), []).append((pid, scope))
        parts = Path(path).parts
        if len(parts) >= 2 and slug.lower() in ("overview", "readme", "index", "_index"):
            by_folder.setdefault(parts[-2].lower(), []).append((pid, scope))
    updates = []
    for lid, from_id, to_slug, label in conn.execute("SELECT id, from_id, to_slug, label FROM links"):
        key = to_slug.strip().lower()
        if key.endswith(".md"):
            key = key[:-3]
        cands, how = by_slug.get(key) or by_slug.get(key.split("/")[-1]) or [], "slug"
        if not cands:
            cands, how = by_title.get(key) or [], "title"
        if not cands:
            cands, how = by_slug.get(slugify(key)) or [], "fuzzy"
        if not cands and label and key in types:
            lk = label.strip().lower()
            cands, how = by_slug.get(lk) or by_slug.get(slugify(lk)) or by_title.get(lk) or [], "label"
        if not cands:
            cands, how = by_folder.get(key) or [], "folder"
        cands = list(dict.fromkeys(cands))
        if len(cands) == 1:
            updates.append((cands[0][0], 0, how, lid))
        elif len(cands) > 1:
            same = [c for c in cands if c[1] == scope_of.get(from_id)]
            updates.append((same[0][0] if len(same) == 1 else cands[0][0], 1, how, lid))
        else:
            updates.append((None, 0, None, lid))
    conn.executemany("UPDATE links SET to_id=?, ambiguous=?, match=? WHERE id=?", updates)


def sync_markdown(conn, root: Path, coll: dict, exclude_keys: set, full: bool, stats: dict) -> None:
    seen = set()
    existing = {p: (h, i) for p, h, i in conn.execute("SELECT path, content_hash, id FROM pages WHERE collection=?", (coll["name"],))}
    for p, rel in iter_collection_files(root, coll):
        data = p.read_bytes()
        chash = sha256_bytes(data)
        seen.add(rel)
        if not full and rel in existing and existing[rel][0] == chash:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
        upsert_page(conn, coll, rel, text, chash, p.stat().st_mtime, exclude_keys)
        stats["changed" if rel in existing else "added"] += 1
    for rel, (_, pid) in existing.items():
        if rel not in seen:
            conn.execute("DELETE FROM pages WHERE id=?", (pid,))
            stats["removed"] += 1


def sync_raw(conn, root: Path, cfg: dict, coll: dict, full: bool, stats: dict) -> None:
    """Load raw documents that pages cite in `sources:`. Statistics of what exists, not guesses."""
    exts = set(coll.get("extensions", [".md", ".txt", ".json", ".csv", ".vtt", ".srt", ".yaml", ".yml"]))
    max_bytes = int(coll.get("max_bytes", 5_000_000))
    wiki_root = root / (cfg.get("wiki", {}).get("root") or ".")
    search_roots = [root, wiki_root, root.parent]
    existing = {p: (h, i) for p, h, i in conn.execute("SELECT path, content_hash, id FROM raw_documents")}
    seen = set()
    for pid, spath in conn.execute("SELECT page_id, source_path FROM sources").fetchall():
        cand = None
        s = spath.strip().strip("[]")
        for base in search_roots:
            c = (base / os.path.expanduser(s)).resolve() if not os.path.isabs(s) else Path(s)
            if c.is_file():
                cand = c
                break
        if cand is None or cand.suffix.lower() not in exts:
            continue
        try:
            rel = cand.relative_to(root.resolve()).as_posix()
        except ValueError:
            rel = cand.as_posix()
        seen.add(rel)
        size = cand.stat().st_size
        if size > max_bytes:
            stats.setdefault("skipped_large", 0)
            stats["skipped_large"] += 1
            continue
        data = cand.read_bytes()
        chash = sha256_bytes(data)
        if rel in existing and existing[rel][0] == chash and not full:
            rid = existing[rel][1]
        else:
            text = data.decode("utf-8", errors="replace")
            title = cand.name
            for line in text.splitlines()[:40]:
                m = HEADING_RE.match(line.strip())
                if m:
                    title = m.group(2).strip()
                    break
            if rel in existing:
                rid = existing[rel][1]
                conn.execute("UPDATE raw_documents SET kind=?, title=?, body=?, bytes=?, content_hash=?, indexed_at=? WHERE id=?",
                             (cand.suffix.lstrip(".").lower(), title, text, size, chash, now_iso(), rid))
                stats["raw_changed"] += 1
            else:
                rid = conn.execute("INSERT INTO raw_documents(path, kind, title, body, bytes, content_hash, indexed_at) VALUES (?,?,?,?,?,?,?)",
                                   (rel, cand.suffix.lstrip(".").lower(), title, text, size, chash, now_iso())).lastrowid
                existing[rel] = (chash, rid)
                stats["raw_added"] += 1
        conn.execute("UPDATE sources SET raw_id=? WHERE page_id=? AND source_path=?", (rid, pid, spath))
    for rel, (_, rid) in list(existing.items()):
        if rel not in seen:
            conn.execute("DELETE FROM raw_documents WHERE id=?", (rid,))
            stats["raw_removed"] += 1


def _infer_type(values: list) -> str:
    nonempty = [v for v in values if v not in (None, "")]
    if not nonempty:
        return "TEXT"
    if all(isinstance(v, bool) for v in nonempty):
        return "INTEGER"
    if all(isinstance(v, int) and not isinstance(v, bool) for v in nonempty):
        return "INTEGER"
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in nonempty):
        return "REAL"
    if all(isinstance(v, str) and re.fullmatch(r"-?\d+", v.strip()) for v in nonempty):
        return "INTEGER"
    if all(isinstance(v, str) and re.fullmatch(r"-?\d+(\.\d+)?", v.strip()) for v in nonempty):
        return "REAL"
    return "TEXT"


def sync_tabular(conn, root: Path, coll: dict, full: bool, stats: dict) -> None:
    """Load a CSV / JSON / JSONL file into its own table (columns inferred; reloaded when the file changes)."""
    path = root / coll["path"]
    table = ident(coll.get("table") or Path(coll["path"]).stem)
    if not path.exists():
        stats.setdefault("missing", []).append(coll["path"])
        return
    data = path.read_bytes()
    chash = sha256_bytes(data)
    key = f"tabular:{table}"
    if not full and get_state(conn, key) == chash:
        # data unchanged, but the docs live in config.json and may have been edited since — republish
        # them every sync so SCHEMA.md never lags a `doc` / `column_docs` change
        _write_tabular_docs(conn, table, coll, count_rows(conn, table))
        return
    kind = coll.get("kind") or path.suffix.lstrip(".").lower()
    text = data.decode("utf-8-sig", errors="replace")
    rows: list[dict] = []
    if kind == "csv":
        rows = list(csv.DictReader(io.StringIO(text)))
    elif kind == "tsv":
        rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
    elif kind == "jsonl":
        rows = [json.loads(l) for l in text.splitlines() if l.strip()]
    elif kind == "json":
        obj = json.loads(text)
        if isinstance(obj, dict):
            for k in coll.get("root_keys", []) or [k for k, v in obj.items() if isinstance(v, list)][:1]:
                obj = obj[k]
                break
        rows = obj if isinstance(obj, list) else [obj]
    else:
        stats.setdefault("unsupported", []).append(coll["path"])
        return
    rows = [r for r in rows if isinstance(r, dict)]
    cols: dict[str, str] = {}
    for r in rows:
        for k in r.keys():
            cols.setdefault(k, ident(k))
    types = {ck: _infer_type([r.get(k) for r in rows]) for k, ck in cols.items()}
    conn.execute(f'DROP TABLE IF EXISTS "{table}"')
    coldefs = ", ".join(f'"{ck}" {types[ck]}' for ck in cols.values())
    conn.execute(f'CREATE TABLE "{table}" (_row INTEGER PRIMARY KEY, {coldefs})')
    placeholders = ", ".join("?" for _ in cols)
    for r in rows:
        vals = []
        for k, ck in cols.items():
            v = r.get(k)
            if isinstance(v, (dict, list)):
                v = json.dumps(v, ensure_ascii=False)
            elif isinstance(v, bool):
                v = int(v)
            elif v == "" and types[ck] != "TEXT":
                v = None
            vals.append(v)
        conn.execute(f'INSERT INTO "{table}" ({", ".join(chr(34)+c+chr(34) for c in cols.values())}) VALUES ({placeholders})', vals)
    _write_tabular_docs(conn, table, coll, len(rows))
    set_state(conn, key, chash)
    stats["tabular_reloaded"] += 1


def count_rows(conn, table: str) -> int:
    try:
        return conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    except sqlite3.Error:
        return 0


def _write_tabular_docs(conn, table: str, coll: dict, nrows: int) -> None:
    """Tabular docs come only from config.json, so replace them wholesale: edits show up, removed docs disappear."""
    conn.execute("DELETE FROM column_docs WHERE object=?", (table,))
    conn.execute("INSERT INTO column_docs(object, column, doc) VALUES (?,?,?)",
                 (table, "_", coll.get("doc") or f"loaded from {coll['path']} ({nrows} rows); columns inferred from the file"))
    for k, d in (coll.get("column_docs") or {}).items():
        conn.execute("INSERT OR REPLACE INTO column_docs(object, column, doc) VALUES (?,?,?)", (table, ident(k), d))


def sync_log(conn, root: Path, cfg: dict) -> None:
    log_rel = cfg.get("wiki", {}).get("log")
    if not log_rel or not (root / log_rel).exists():
        return
    text = (root / log_rel).read_text(encoding="utf-8", errors="replace")
    _, body = split_frontmatter(text)
    conn.execute("DELETE FROM log_entries")
    entries, cur, buf = [], None, []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            if cur is not None:
                entries.append((cur, "\n".join(buf).strip()))
            cur, buf = m.group(1).strip(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        entries.append((cur, "\n".join(buf).strip()))
    for i, (title, b) in enumerate(entries):
        dm = re.search(r"\d{4}-\d{2}-\d{2}", title)
        conn.execute("INSERT INTO log_entries(ord, date, title, body) VALUES (?,?,?,?)", (i, dm.group(0) if dm else None, title, b))


def load_template_docs(root: Path, cfg: dict) -> dict[str, dict[str, str | None]]:
    """type → {key: doc-or-None} from the wiki's page templates. The key ORDER is the template's."""
    out: dict[str, dict] = {}
    tdir = cfg.get("wiki", {}).get("templates")
    if not tdir or not (root / tdir).is_dir():
        return out
    for p in sorted((root / tdir).glob("*.md")):
        fm_text, _ = split_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        if fm_text is None:
            continue
        data, docs = parse_yaml_subset(fm_text)
        t = data.get("type") if isinstance(data, dict) else None
        t = (str(t).strip().lower() if t else p.stem.lower())
        out[t] = {k: docs.get(k) for k in (data.keys() if isinstance(data, dict) else [])}
    return out


def load_ontology_engine(root: Path):
    """The vendored project-ontology engine, imported by path; None when the skill is not installed."""
    path = root / ONTOLOGY_ENGINE_REL
    if not path.exists():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("project_ontology_engine", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ontology_snapshot(root: Path) -> dict | None:
    """What project-ontology says about the project right now (terms, bindings, page ids, violations).
    None without the skill; {"error": …} when it cannot be loaded — reported, never fatal to a sync."""
    try:
        mod = load_ontology_engine(root)
    except Exception as e:  # a broken vendored engine must not take the database down with it
        return {"error": f"ontology engine failed to import: {type(e).__name__}: {e}"}
    if mod is None:
        return None
    if getattr(mod, "API_VERSION", None) != ONTOLOGY_API:
        return {"error": f"ontology engine API {getattr(mod, 'API_VERSION', None)} ≠ {ONTOLOGY_API} expected — re-run /ontology:init to re-vendor it"}
    try:
        return mod.load_for_db(root)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def sync_ontology(conn, root: Path, cfg: dict, snap: dict | None) -> dict:
    for tbl in ("ontology_terms", "ontology_aliases", "ontology_fields", "ontology_violations"):
        conn.execute(f"DELETE FROM {tbl}")
    conn.execute("UPDATE pages SET ontology_id = NULL WHERE ontology_id IS NOT NULL")
    gate = (cfg.get("ontology") or {}).get("gate", "warn")
    if snap is None:
        state = {"present": False}
        set_state(conn, "ontology", state)
        return state
    if snap.get("error"):
        state = {"present": True, "error": snap["error"], "file": snap.get("file"), "gate": gate}
        set_state(conn, "ontology", state)
        return state
    cols = ("id", "kind", "namespace", "parent", "value", "label", "definition", "status", "replaced_by", "since",
            "approved_by", "approved_on", "source", "domain", "range")
    conn.executemany(f"INSERT OR REPLACE INTO ontology_terms({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
                     [tuple(tm.get(c) for c in cols) for tm in snap["terms"]])
    conn.executemany("INSERT OR IGNORE INTO ontology_aliases(alias, term_id, status) VALUES (?,?,?)",
                     [(a["alias"], a["term_id"], a["status"]) for a in snap["aliases"]])
    conn.executemany("INSERT OR REPLACE INTO ontology_fields(binding, type, field, kind, namespace, relation) VALUES (?,?,?,?,?,?)",
                     [(f["binding"], f["type"], f["field"], f["kind"], f.get("namespace"), f.get("relation")) for f in snap["fields"]])
    roots = {c["name"]: str(c.get("root", ".")).strip("/") for c in cfg.get("collections", []) if c.get("kind", "markdown") == "markdown"}
    pmap = {}
    for pid, coll, path in conn.execute("SELECT id, collection, path FROM pages").fetchall():
        base = roots.get(coll, "")
        pmap[path if base in ("", ".") else f"{base}/{path}"] = (pid, path)
    conn.executemany("UPDATE pages SET ontology_id=? WHERE id=?",
                     [(info["id"], pmap[rel][0]) for rel, info in snap["pages"].items() if rel in pmap])
    rows = []
    for v in snap["violations"]:
        pid, ppath = pmap.get(v["path"], (None, v["path"]))
        rows.append((pid, ppath, v.get("line"), v["rule"], v["policy"], v.get("family"), v.get("field"),
                     None if v.get("value") is None else str(v["value"]), v["message"], v.get("suggestion"),
                     ", ".join(v.get("nearest") or []) or None))
    conn.executemany("INSERT INTO ontology_violations(page_id, path, line, rule, policy, family, field, value, message, suggestion, nearest) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    s = snap.get("summary", {})
    state = {"present": True, "file": snap.get("file"), "policy": snap.get("policy"), "gate": gate, "errors": snap.get("errors", []),
             "terms": s.get("terms", 0), "approved": s.get("approved", 0), "proposed": s.get("proposed", 0), "deprecated": s.get("deprecated", 0),
             "violations": s.get("violations", 0), "strict": s.get("strict", 0), "warn": s.get("warn", 0), "by_rule": s.get("by_rule", {})}
    set_state(conn, "ontology", state)
    return state


def ontology_column_docs(snap: dict | None, ptype: str) -> dict[str, str]:
    """column → doc for a typed view, naming the binding and its approved values — the schema-as-prompt
    then shows the controlled vocabulary instead of a template comment that may have drifted."""
    if not snap or snap.get("error"):
        return {}
    by_parent: dict[str, list] = {}
    for tm in snap["terms"]:
        by_parent.setdefault(tm["parent"], []).append(tm)
    out = {}
    for f in snap["fields"]:
        if f["type"] not in (ptype, "*") or f["field"] in ("type",):
            continue
        kind = f["kind"]
        if kind == "vocab":
            parent = f"{ptype}.{f['field']}"
            terms = by_parent.get(parent, [])
            appr = [tm["value"] for tm in terms if tm["status"] == "approved"]
            prop = [tm["value"] for tm in terms if tm["status"] == "proposed"]
            doc = f"→ {parent}: " + ("|".join(appr) or "(none approved)") + (f" (proposed: {'|'.join(prop)})" if prop else "")
        elif kind == "entity":
            ents = [tm["value"] for tm in by_parent.get(f.get("namespace") or "", []) if tm["status"] == "approved"]
            doc = f"→ {f.get('namespace')}.* entities: " + ("|".join(ents[:12]) or "—")
        elif kind == "relation":
            rel = next((tm for tm in snap["terms"] if tm["id"] == f.get("relation")), {})
            doc = f"→ {f.get('relation')}: [[link]] to {rel.get('range') or 'any'} pages"
        else:
            continue
        out[f["field"]] = doc
    return out


def regen_views(conn, cfg: dict, tdocs: dict, snap: dict | None = None) -> list[str]:
    """One view per page type: base columns + every frontmatter key seen on that type as a real column."""
    prev = get_state(conn, "generated_views")
    for name in (json.loads(prev) if prev else []):
        conn.execute(f'DROP VIEW IF EXISTS "{name}"')
    created = []
    scope_alias = "client"
    for coll in cfg.get("collections", []):
        if coll.get("kind") == "markdown" and coll.get("scope_field"):
            scope_alias = ident(coll["scope_field"])
    skip = set(cfg.get("view_exclude_types", ["index", "log", "lint-report"]))
    types = [r[0] for r in conn.execute("SELECT DISTINCT type FROM pages WHERE type IS NOT NULL ORDER BY type") if r[0] not in skip]
    for t in types:
        keys: list[str] = list((tdocs.get(t) or {}).keys())
        for (k,) in conn.execute("SELECT DISTINCT key FROM page_fields pf JOIN pages p ON p.id=pf.page_id WHERE p.type=? ORDER BY key", (t,)):
            if k not in keys:
                keys.append(k)
        cols = []
        used = {"id", "path", "slug", "ontology_id", "title", scope_alias, "status", "created", "updated", "body", "word_count", "type", "frontmatter"}
        for k in keys:
            if k in BASE_KEYS or k in MULTI_KEYS:
                continue
            c = ident(k)
            if c in used:
                continue
            used.add(c)
            cols.append(f"json_extract(frontmatter, '$.\"{k}\"') AS \"{c}\"")
        vname = ident(plural(t))
        if vname in {"pages", "links", "tags", "sources", "sections", "raw_documents", "log_entries", "column_docs", "sync_state", "page_fields"}:
            vname = f"{vname}_v"
        extra = (",\n  " + ",\n  ".join(cols)) if cols else ""
        # `frontmatter` stays available on the view so json_extract(frontmatter, '$.any-key') keeps
        # working when an agent reaches for a key the view did not surface (an eval agent hit
        # "no such column: frontmatter" on the gaps view and had to fall back to pages)
        conn.execute(f'CREATE VIEW "{vname}" AS SELECT id, path, slug, ontology_id, title, scope AS "{scope_alias}", status{extra},\n  created, updated, word_count, body, frontmatter FROM pages WHERE type = {sql_str(t)}')
        created.append(vname)
        n = conn.execute("SELECT COUNT(*) FROM pages WHERE type=?", (t,)).fetchone()[0]
        conn.execute("INSERT OR REPLACE INTO column_docs(object, column, doc) VALUES (?,?,?)",
                     (vname, "_", f"typed view over pages WHERE type='{t}' ({n} rows); frontmatter keys as columns"))
        conn.execute("INSERT OR REPLACE INTO column_docs(object, column, doc) VALUES (?,?,?)",
                     (vname, scope_alias, "frontmatter scope (pages.scope)"))
        for k, doc in (tdocs.get(t) or {}).items():
            if doc and k not in BASE_KEYS and k not in MULTI_KEYS:
                conn.execute("INSERT OR REPLACE INTO column_docs(object, column, doc) VALUES (?,?,?)", (vname, ident(k), doc))
            elif doc and k == "status":
                conn.execute("INSERT OR REPLACE INTO column_docs(object, column, doc) VALUES (?,?,?)", (vname, "status", doc))
        for k, doc in ontology_column_docs(snap, t).items():
            col = scope_alias if k == scope_alias else ("status" if k == "status" else ident(k))
            conn.execute("INSERT OR REPLACE INTO column_docs(object, column, doc) VALUES (?,?,?)", (vname, col, doc))
    set_state(conn, "generated_views", created)
    return created


def apply_curated_views(conn, path: Path) -> tuple[list[str], list[str]]:
    """Apply .claude/db/views.sql: every CREATE VIEW is dropped+recreated; failures are reported, not fatal."""
    ok, bad = [], []
    if not path.exists():
        return ok, bad
    text = path.read_text(encoding="utf-8")
    for stmt in split_sql(text):
        # statements may start with comment lines (the file's own header); search the code only,
        # otherwise prose like "every CREATE VIEW below" in a comment would be taken for a view name
        m = re.search(r"CREATE\s+VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`]?([A-Za-z0-9_]+)[\"`]?", strip_strings(stmt), re.I)
        if not m:
            continue
        name = m.group(1)
        try:
            conn.execute(f'DROP VIEW IF EXISTS "{name}"')
            conn.execute(stmt)
            ok.append(name)
            conn.execute("INSERT OR REPLACE INTO column_docs(object, column, doc) VALUES (?,?,?)",
                         (name, "_", view_doc(stmt) or "curated view from .claude/db/views.sql"))
        except sqlite3.Error as e:
            bad.append(f"{name}: {e}")
    set_state(conn, "curated_views", ok)
    return ok, bad


def view_doc(stmt: str) -> str | None:
    """The `-- doc:` line that belongs to this view: the first one at or after the CREATE VIEW *code*
    line. The file header (comment lines that ride along with the first statement) may mention
    `-- doc:` in prose, and must never become the first view's description."""
    for cv in re.finditer(r"CREATE\s+VIEW", stmt, re.I):
        line_start = stmt.rfind("\n", 0, cv.start()) + 1
        if stmt[line_start:cv.start()].lstrip().startswith("--"):
            continue  # inside a comment line
        dm = re.search(r"--\s*doc:\s*(.+)", stmt[cv.start():])
        return dm.group(1).strip() if dm else None
    return None


def split_sql(text: str) -> list[str]:
    """Split SQL text on ';' outside strings/comments. Returns non-empty statements (no trailing ';')."""
    out, buf, i, n = [], [], 0, len(text)
    q = None
    while i < n:
        ch = text[i]
        if q:
            buf.append(ch)
            if ch == q:
                q = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            q = ch
            buf.append(ch)
            i += 1
            continue
        if text.startswith("--", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            buf.append(text[i:j])
            i = j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            i = j
            continue
        if ch == ";":
            s = "".join(buf).strip()
            if s and not all(l.strip().startswith("--") or not l.strip() for l in s.splitlines()):
                out.append(s)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    s = "".join(buf).strip()
    if s and not all(l.strip().startswith("--") or not l.strip() for l in s.splitlines()):
        out.append(s)
    return out


def rebuild_fts(conn) -> None:
    if not fts_available(conn):
        return
    conn.execute("INSERT INTO pages_fts(pages_fts) VALUES ('rebuild')")
    conn.execute("INSERT INTO raw_fts(raw_fts) VALUES ('rebuild')")


# ----------------------------------------------------------------------------- schema summary (schema-as-prompt)

def table_columns(conn, name: str) -> list[str]:
    return [r[1] for r in conn.execute(f'PRAGMA table_info("{name}")')]


def schema_markdown(conn, cfg: dict, root: Path) -> str:
    docs: dict[str, dict[str, str]] = {}
    for obj, col, doc in conn.execute("SELECT object, column, doc FROM column_docs"):
        docs.setdefault(obj, {})[col] = doc
    q = cfg.get("query", {})
    mode = cfg.get("mode", "local")
    last = get_state(conn, "last_sync") or "never"
    npages = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    nraw = conn.execute("SELECT COUNT(*) FROM raw_documents").fetchone()[0]
    out = [f"# project-db schema — {cfg.get('slug')} ({mode}) — synced {last} — {npages} pages, {nraw} raw documents", ""]
    out.append("Query: `python3 .claude/db/db.py query \"<one SELECT>\"` → CSV. Rules: read-only · "
               f"{q.get('row_limit', 200)}-row cap (add LIMIT/WHERE) · {q.get('timeout_seconds', 5)} s timeout · "
               f"cells truncated at {q.get('max_cell_chars', 400)} chars (`--max-cell 0` for full text) · every query is audited.")
    out.append("")
    gen = json.loads(get_state(conn, "generated_views") or "[]")
    cur = json.loads(get_state(conn, "curated_views") or "[]")
    if gen:
        out.append("## Typed views (one per page type — start here)")
        for v in gen:
            n = conn.execute(f'SELECT COUNT(*) FROM "{v}"').fetchone()[0]
            cols = table_columns(conn, v)
            out.append(f"- **{v}**({', '.join(cols)}) — {n} rows")
            d = docs.get(v, {})
            hints = [f"{c}: {d[c]}" for c in cols if c in d and c not in ("_", "client", "scope")]
            if hints:
                out.append("  - " + " · ".join(hints))
        out.append("")
    if cur:
        out.append("## Curated views (.claude/db/views.sql — add your own)")
        for v in cur:
            try:
                n = conn.execute(f'SELECT COUNT(*) FROM "{v}"').fetchone()[0]
            except sqlite3.Error:
                n = "?"
            out.append(f"- **{v}**({', '.join(table_columns(conn, v))}) — {n} rows — {docs.get(v, {}).get('_', '')}")
        out.append("")
    out.append("## Base tables")
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts%' ORDER BY name")]
    for t in tables:
        n = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        d = docs.get(t, {})
        out.append(f"- **{t}**({', '.join(table_columns(conn, t))}) — {n} rows. {d.get('_', '')}")
        hints = [f"{c}: {d[c]}" for c in table_columns(conn, t) if c in d]
        if hints:
            out.append("  - " + " · ".join(hints))
    out.append("")
    if fts_available(conn):
        out.append("## Full-text search")
        out.append("```sql\nSELECT p.slug, p.type, snippet(pages_fts, 1, '[', ']', '…', 12) AS hit\nFROM pages_fts JOIN pages p ON p.id = pages_fts.rowid\nWHERE pages_fts MATCH 'budget AND approval' LIMIT 20;\n-- raw_fts works the same over raw_documents\n```")
        out.append("")
    ost = json.loads(get_state(conn, "ontology") or "{}")
    if ost.get("present"):
        out.append(f"## Ontology — controlled vocabulary ({ost.get('file') or 'project-ontology'})")
        if ost.get("error"):
            out.append(f"- ⚠ not loaded: {ost['error']}")
        else:
            pol = ost.get("policy") or {}
            out.append(f"- {ost.get('terms', 0)} terms ({ost.get('approved', 0)} approved · {ost.get('proposed', 0)} proposed · {ost.get('deprecated', 0)} deprecated) · "
                       f"policy {pol.get('default', '?')} · {ost.get('violations', 0)} open violations (strict {ost.get('strict', 0)} · warn {ost.get('warn', 0)}) · sync gate {ost.get('gate', 'warn')}")
            out.append("- Legal values: `SELECT value, status FROM ontology_terms WHERE parent = 'gap.severity' ORDER BY rowid` · controlled fields: `ontology_fields`")
            out.append("- What is broken: `SELECT rule, policy, path, field, value, suggestion FROM ontology_violations ORDER BY policy DESC, path`")
            out.append("- Subtrees by derived id: `SELECT slug, ontology_id FROM pages WHERE ontology_id LIKE 'client.acme.%'` (typed views carry `ontology_id` too)")
            out.append("- Pages keep plain values; the write hook blocks unregistered ones — change terms with /ontology:propose, not in the database")
        out.append("")
    out.append("## Patterns")
    out.append("- Any frontmatter key: `SELECT p.slug FROM page_fields f JOIN pages p ON p.id=f.page_id WHERE f.key='resolution-approach' AND f.value='custom-dev'`")
    out.append("- Backlinks: `SELECT s.slug FROM links l JOIN pages s ON s.id=l.from_id JOIN pages t ON t.id=l.to_id WHERE t.slug='budget-management'`")
    out.append("- One section: `SELECT content FROM sections s JOIN pages p ON p.id=s.page_id WHERE p.slug='x' AND s.heading LIKE 'Current%'`")
    out.append("- Read the full page after finding it: the wiki file at pages.path is the record; the DB is the index.")
    return "\n".join(out) + "\n"


def write_schema_md(conn, cfg, root) -> str:
    md = schema_markdown(conn, cfg, root)
    (root / DB_DIR_REL / "SCHEMA.md").write_text(md, encoding="utf-8")
    set_state(conn, "schema_md", md)
    return md


# ----------------------------------------------------------------------------- sync / build

def open_rw(root: Path, cfg: dict) -> sqlite3.Connection:
    db_path = root / cfg["db_path"]
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def do_sync(root: Path, cfg: dict, full: bool) -> dict:
    snap = ontology_snapshot(root)  # read before the write transaction: it only reads files
    conn = open_rw(root, cfg)
    stats = {"added": 0, "changed": 0, "removed": 0, "raw_added": 0, "raw_changed": 0, "raw_removed": 0, "tabular_reloaded": 0}
    t0 = time.time()
    with conn:
        stored_ver = get_state(conn, "schema_version") if conn.execute("SELECT name FROM sqlite_master WHERE name='sync_state'").fetchone() else None
        if full or (stored_ver is not None and int(stored_ver) != SCHEMA_VERSION):
            for (name, typ) in conn.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'").fetchall():
                conn.execute(f'DROP {"VIEW" if typ == "view" else "TABLE"} IF EXISTS "{name}"')
            full = True
        ensure_schema(conn)
        exclude_keys = set(cfg.get("exclude_keys", []))
        for coll in cfg.get("collections", []):
            kind = coll.get("kind", "markdown")
            if kind == "markdown":
                sync_markdown(conn, root, coll, exclude_keys, full, stats)
        resolve_links(conn)
        for coll in cfg.get("collections", []):
            if coll.get("kind") == "raw":
                sync_raw(conn, root, cfg, coll, full, stats)
        for coll in cfg.get("tabular", []):
            sync_tabular(conn, root, coll, full, stats)
        sync_log(conn, root, cfg)
        onto_state = sync_ontology(conn, root, cfg, snap)
        tdocs = load_template_docs(root, cfg)
        gen = regen_views(conn, cfg, tdocs, snap)
        ok, bad = apply_curated_views(conn, root / DB_DIR_REL / "views.sql")
        changed = sum(v for k, v in stats.items() if isinstance(v, int))
        if changed or full:
            rebuild_fts(conn)
        set_state(conn, "schema_version", SCHEMA_VERSION)
        set_state(conn, "engine_version", ENGINE_VERSION)
        set_state(conn, "mode", cfg.get("mode", "local"))
        set_state(conn, "slug", cfg.get("slug", ""))
        set_state(conn, "last_sync", now_iso())
        if full:
            set_state(conn, "last_build", now_iso())
        set_state(conn, "last_sync_changes", changed)
        set_state(conn, "counts", {
            "pages": conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0],
            "raw_documents": conn.execute("SELECT COUNT(*) FROM raw_documents").fetchone()[0],
            "links": conn.execute("SELECT COUNT(*) FROM links").fetchone()[0],
            "broken_links": conn.execute("SELECT COUNT(*) FROM links WHERE to_id IS NULL").fetchone()[0],
            "by_type": dict(conn.execute("SELECT type, COUNT(*) FROM pages WHERE type IS NOT NULL GROUP BY type ORDER BY 2 DESC").fetchall()),
        })
        write_schema_md(conn, cfg, root)
    stats.update({"generated_views": gen, "curated_views_ok": ok, "curated_views_failed": bad, "ontology": onto_state,
                  "seconds": round(time.time() - t0, 2), "full": full})
    conn.close()
    return stats


def banner(root: Path, cfg: dict, stats: dict | None = None) -> str:
    conn = sqlite3.connect(f"file:{root / cfg['db_path']}?mode=ro", uri=True)
    counts = json.loads(get_state(conn, "counts") or "{}")
    last = get_state(conn, "last_sync") or "never"
    by_type = counts.get("by_type", {})
    conn.close()
    parts = [f"{counts.get('pages', 0)} pages"] + [f"{n} {plural(t)}" for t, n in list(by_type.items())[:6]]
    if counts.get("raw_documents"):
        parts.append(f"{counts['raw_documents']} raw docs")
    chg = ""
    if stats:
        n = stats["added"] + stats["changed"] + stats["removed"]
        chg = f" · synced now ({n} changed)" if n else " · up to date"
    mode = cfg.get("mode", "local")
    lines = [f"🗄 project-db [{cfg.get('slug')}, {mode}]: " + " · ".join(parts) + chg,
             "  query:  python3 .claude/db/db.py query \"SELECT …\"   (read-only, CSV, 200-row cap)",
             "  schema: .claude/db/SCHEMA.md  ·  views: .claude/db/views.sql  ·  refresh: /db:sync"]
    ost = (stats or {}).get("ontology") or json.loads(get_state_ro(root, cfg, "ontology") or "{}")
    if ost.get("present"):
        lines.append("  ontology: " + (f"⚠ not loaded — {ost['error']}" if ost.get("error") else
                     f"{ost.get('terms', 0)} terms · {ost.get('violations', 0)} violations (strict {ost.get('strict', 0)}) → SELECT * FROM ontology_violations"))
    if mode in ("d1", "both"):
        lines.append(f"  remote: D1 `{cfg.get('d1', {}).get('database_name', '?')}` · last publish {get_state_ro(root, cfg, 'last_publish') or 'never'} · /db:publish")
    return "\n".join(lines)


def get_state_ro(root, cfg, key):
    try:
        conn = sqlite3.connect(f"file:{root / cfg['db_path']}?mode=ro", uri=True)
        v = get_state(conn, key)
        conn.close()
        return v
    except sqlite3.Error:
        return None


# ----------------------------------------------------------------------------- query guardrails

_ALLOWED_ACTIONS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
if hasattr(sqlite3, "SQLITE_RECURSIVE"):
    _ALLOWED_ACTIONS.add(sqlite3.SQLITE_RECURSIVE)

FORBIDDEN_RE = re.compile(r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum|reindex|begin|commit|rollback|savepoint|release)\b", re.I)


def strip_strings(sql: str) -> str:
    return re.sub(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|--[^\n]*|/\*.*?\*/", " ", sql, flags=re.S)


def validate_sql(sql: str) -> str:
    """Belt (this) and braces (the authorizer). Returns the single trimmed statement or raises ValueError."""
    stmts = split_sql(sql)
    if len(stmts) != 1:
        raise ValueError(f"exactly one statement per call (got {len(stmts)})")
    s = stmts[0]
    head = strip_strings(s).lstrip().lower()
    if not re.match(r"(select|with|explain)\b", head):
        raise ValueError("only SELECT / WITH … SELECT / EXPLAIN QUERY PLAN are allowed (the database is read-only; edit the sources and run /db:sync)")
    m = FORBIDDEN_RE.search(strip_strings(s))
    if m and not (head.startswith("with") and m.group(1).lower() in ("replace",)):
        raise ValueError(f"'{m.group(1)}' is not allowed in a read-only query")
    return s


# data_version is what FTS5 reads to detect content changes; the rest are schema introspection
_SAFE_PRAGMAS = {"data_version", "table_info", "table_xinfo", "table_list", "index_list", "index_info", "index_xinfo", "foreign_key_list", "compile_options"}


def _authorizer(action, arg1, arg2, dbname, trigger):
    if action in _ALLOWED_ACTIONS:
        return sqlite3.SQLITE_OK
    # schema introspection pragmas are reads; everything else (journal_mode, writable_schema…) is not
    if action == sqlite3.SQLITE_PRAGMA and (arg1 or "").lower() in _SAFE_PRAGMAS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def open_ro(root: Path, cfg: dict, timeout_s: float) -> sqlite3.Connection:
    db_path = root / cfg["db_path"]
    if not db_path.exists():
        die(f"database not built yet: {db_path} — run /db:sync")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2)
    conn.set_authorizer(_authorizer)
    deadline = time.monotonic() + timeout_s
    conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 5000)
    return conn


def audit_write(root: Path, cfg: dict, rec: dict) -> None:
    try:
        path = root / cfg.get("audit_path", f"{DB_DIR_REL}/audit.sqlite")
        conn = sqlite3.connect(str(path), timeout=5)
        conn.execute("""CREATE TABLE IF NOT EXISTS query_log (
  id INTEGER PRIMARY KEY, ts TEXT NOT NULL, actor TEXT, session TEXT, target TEXT, sql TEXT NOT NULL,
  rows INTEGER, ms INTEGER, truncated INTEGER NOT NULL DEFAULT 0, error TEXT)""")
        conn.execute("INSERT INTO query_log(ts, actor, session, target, sql, rows, ms, truncated, error) VALUES (?,?,?,?,?,?,?,?,?)",
                     (now_iso(), rec.get("actor"), rec.get("session"), rec.get("target", "local"), rec["sql"],
                      rec.get("rows"), rec.get("ms"), int(bool(rec.get("truncated"))), rec.get("error")))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:  # auditing must never break a query, but must not fail silently either
        print(f"warning: audit log not written ({e})", file=sys.stderr)


def truncate_cell(v, max_chars: int):
    if v is None:
        return ""
    if isinstance(v, bytes):
        return f"<blob {len(v)} bytes>"
    s = str(v)
    if max_chars and len(s) > max_chars:
        return s[:max_chars] + f"…[+{len(s) - max_chars} chars]"
    return s


def format_rows(cols: list[str], rows: list, fmt: str, max_chars: int) -> str:
    if fmt == "json":
        return json.dumps([{c: (r[i] if not isinstance(r[i], bytes) else truncate_cell(r[i], 0)) if not (isinstance(r[i], str) and max_chars and len(r[i]) > max_chars) else truncate_cell(r[i], max_chars) for i, c in enumerate(cols)} for r in rows], ensure_ascii=False, indent=1)
    if fmt == "md":
        lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
        for r in rows:
            lines.append("| " + " | ".join(truncate_cell(v, max_chars).replace("|", "\\|").replace("\n", " ") for v in r) + " |")
        return "\n".join(lines)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    for r in rows:
        w.writerow([truncate_cell(v, max_chars) for v in r])
    return buf.getvalue().rstrip("\n")


_FTS_OPERATOR_RE = re.compile(r'"|\*|\bAND\b|\bOR\b|\bNOT\b|\bNEAR\b|:|\(|\)|\^')


def fts_terms(terms: str) -> str:
    """FTS5 reads `co-op` as `co` minus a column called `op`. If the user wrote no FTS syntax of their
    own, quote each token so punctuation is literal and tokens are implicitly ANDed."""
    if _FTS_OPERATOR_RE.search(terms):
        return terms
    toks = [t for t in re.split(r"\s+", terms.strip()) if t]
    if all(re.fullmatch(r"[\w]+", t) for t in toks):
        return terms
    return " ".join('"' + t.replace('"', '""') + '"' for t in toks)


def ontology_spellings(conn: sqlite3.Connection, terms: str) -> list[str]:
    """Other spellings of the same ontology term: searching "Acme Corp" also finds pages that wrote the
    canonical `acme-corp`, and searching the canonical value finds pages still using an alias."""
    try:
        rows = conn.execute(
            "SELECT t.value, a.alias FROM ontology_aliases a JOIN ontology_terms t ON t.id = a.term_id "
            "WHERE lower(a.alias) = lower(?) OR lower(t.value) = lower(?)", (terms.strip(), terms.strip())).fetchall()
    except sqlite3.Error:
        return []
    out = []
    for value, alias in rows:
        for s in (value, alias):
            if s and s.strip().lower() != terms.strip().lower() and s not in out:
                out.append(s)
    return out


def fts_search(conn: sqlite3.Connection, terms: str, type_: str | None, limit: int, include_raw: bool) -> tuple[list[str], list]:
    """Shared by the CLI `search` and the MCP `db_search`: one implementation, one behaviour."""
    cols = ["slug", "type", "client", "hit"]
    if not fts_available(conn) or not conn.execute("SELECT name FROM sqlite_master WHERE name='pages_fts'").fetchone():
        like = f"%{terms}%"
        rows = conn.execute("SELECT slug, type, scope, substr(body, max(1, instr(body, ?) - 60), 140) FROM pages WHERE body LIKE ? OR title LIKE ? LIMIT ?",
                            (terms, like, like, limit)).fetchall()
        return cols, rows
    q = fts_terms(terms)
    alts = ontology_spellings(conn, terms)
    if alts and not _FTS_OPERATOR_RE.search(terms):
        q = " OR ".join([f"({q})"] + ['"' + a.replace('"', '""') + '"' for a in alts])
    sql = ("SELECT p.slug, p.type, p.scope, snippet(pages_fts, 1, '[', ']', '…', 14) FROM pages_fts JOIN pages p ON p.id = pages_fts.rowid "
           "WHERE pages_fts MATCH ?" + (" AND p.type = ?" if type_ else "") + " ORDER BY rank LIMIT ?")
    params = (q, type_, limit) if type_ else (q, limit)
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        # user-written syntax that FTS5 rejected: retry as one literal phrase before giving up
        rows = conn.execute(sql, (('"' + terms.replace('"', '""') + '"',) + params[1:])).fetchall()
    if include_raw:
        rows += [(p, "raw:" + k, None, h) for p, k, h in conn.execute(
            "SELECT r.path, r.kind, snippet(raw_fts, 1, '[', ']', '…', 14) FROM raw_fts JOIN raw_documents r ON r.id = raw_fts.rowid WHERE raw_fts MATCH ? ORDER BY rank LIMIT ?",
            (q, limit)).fetchall()]
    return cols, rows


def run_query_local(root: Path, cfg: dict, sql: str, limit: int, timeout_s: float) -> tuple[list[str], list, bool, int]:
    conn = open_ro(root, cfg, timeout_s)
    t0 = time.time()
    try:
        cur = conn.execute(sql)
        rows = cur.fetchmany(limit + 1) if limit else cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e).lower():
            raise TimeoutError(f"statement timeout after {timeout_s}s — narrow it with WHERE / LIMIT or a smaller join")
        raise
    finally:
        conn.close()
    truncated = bool(limit) and len(rows) > limit
    if truncated:
        rows = rows[:limit]
    return cols, rows, truncated, int((time.time() - t0) * 1000)


def run_query_remote(cfg: dict, sql: str, limit: int) -> tuple[list[str], list, bool, int]:
    d1 = cfg.get("d1") or {}
    name = d1.get("database_name")
    if not name:
        die("no D1 database configured — run /db:publish first (or /db:init with --mode d1|both)")
    wrapped = sql
    if limit and not strip_strings(sql).lstrip().lower().startswith("explain"):
        wrapped = f"SELECT * FROM ({sql}) LIMIT {limit + 1}"
    t0 = time.time()
    proc = subprocess.run(["npx", "--yes", "wrangler", "d1", "execute", name, "--remote", "--json", "--command", wrapped],
                          capture_output=True, text=True, cwd=str(Path(d1.get("worker_dir", DB_DIR_REL + "/worker"))) if Path(d1.get("worker_dir", "")).exists() else None)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip()[-2000:])
    out = json.loads(proc.stdout[proc.stdout.find("["):])
    results = out[0].get("results", []) if out else []
    cols = list(results[0].keys()) if results else []
    rows = [tuple(r.get(c) for c in cols) for r in results]
    truncated = bool(limit) and len(rows) > limit
    return cols, rows[:limit] if limit else rows, truncated, int((time.time() - t0) * 1000)


# ----------------------------------------------------------------------------- install (vendoring + mandates)

def merge_managed_block(path: Path, block: str) -> str:
    """Insert/replace the sentinel-delimited block. Returns 'created' | 'updated' | 'unchanged'."""
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


def install(root: Path, cfg: dict, skill_dir: Path, has_wiki: bool) -> dict:
    tpl = skill_dir / "templates"
    if not (tpl / "sessionstart-db-hook.sh").exists():
        die(f"skill templates not found under {tpl} — pass --skill-dir <path to skills/project-db>")
    dbdir = root / DB_DIR_REL
    dbdir.mkdir(parents=True, exist_ok=True)
    report = {}
    # 1. vendor the engine itself + local MCP server
    src_engine = Path(__file__).resolve()
    dst_engine = (dbdir / "db.py").resolve()
    if src_engine != dst_engine:
        shutil.copy2(src_engine, dst_engine)
        report["engine"] = f"vendored v{ENGINE_VERSION}"
    shutil.copy2(tpl / "mcp_server.py", dbdir / "mcp_server.py")
    # 2. curated views — seed once, never overwrite (the user owns this file)
    if not (dbdir / "views.sql").exists():
        shutil.copy2(tpl / ("views.wiki.sql" if has_wiki else "views.generic.sql"), dbdir / "views.sql")
        report["views.sql"] = "seeded"
    # 3. hook
    hook_path = root / HOOK_REL
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tpl / "sessionstart-db-hook.sh", hook_path)
    hook_path.chmod(0o755)

    # "$CLAUDE_PROJECT_DIR" quoted: an unquoted project path with a space makes the hook exit 127, which
    # Claude Code treats as a non-blocking error — the banner (and the sync) would silently stop.
    command = f'"$CLAUDE_PROJECT_DIR"/{HOOK_REL}'

    def add_hook(settings):
        hooks = settings.setdefault("hooks", {})
        lst = hooks.setdefault("SessionStart", [])
        found = False
        for entry in lst:
            for h in entry.get("hooks", []):
                if "db-context.sh" in h.get("command", ""):
                    found = True
                    h["command"] = command  # upgrade an older unquoted entry in place
        if not found:
            lst.append({"hooks": [{"type": "command", "command": command, "timeout": 30}]})

    report["settings.json"] = merge_json_file(root / ".claude/settings.json", add_hook)
    # 4. .mcp.json (local stdio MCP over the same guardrails)
    def add_mcp(m):
        servers = m.setdefault("mcpServers", {})
        servers.setdefault("project-db", {"command": "uv", "args": ["run", "--quiet", f"{DB_DIR_REL}/mcp_server.py"]})

    report[".mcp.json"] = merge_json_file(root / ".mcp.json", add_mcp)
    # 5. CLAUDE.md managed block
    block_tpl = (tpl / ("claude-md-block.wiki.md" if has_wiki else "claude-md-block.standalone.md")).read_text(encoding="utf-8")
    q = cfg.get("query", {})
    block = (block_tpl.replace("{{SLUG}}", cfg.get("slug", "")).replace("{{MODE}}", cfg.get("mode", "local"))
             .replace("{{WIKI_ROOT}}", cfg.get("wiki", {}).get("root", "wiki"))
             .replace("{{ROW_LIMIT}}", str(q.get("row_limit", 200))).replace("{{TIMEOUT}}", str(q.get("timeout_seconds", 5)))
             .replace("{{MAX_CELL}}", str(q.get("max_cell_chars", 400))))
    report["CLAUDE.md"] = merge_managed_block(root / "CLAUDE.md", block)
    # 6. .gitignore — the DB is derived; the schema, views, config and engine are committed
    gi = root / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    want = ["# project-db: derived database files (rebuild with /db:sync)", ".claude/db/*.sqlite", ".claude/db/*.sqlite-*", ".claude/db/d1/import.sql"]
    if not any(".claude/db/*.sqlite" in l for l in lines):
        gi.write_text("\n".join(lines + ([""] if lines and lines[-1] else []) + want) + "\n", encoding="utf-8")
        report[".gitignore"] = "updated"
    return report


def detect_wiki(root: Path) -> dict | None:
    for cand in ("wiki", ".claude/wiki", "docs/wiki"):
        w = root / cand
        if (w / "_schema" / "SCHEMA.md").exists() or (w / "_index.md").exists():
            return {"root": cand, "log": f"{cand}/_log.md" if (w / "_log.md").exists() else None,
                    "templates": f"{cand}/_schema/templates" if (w / "_schema" / "templates").is_dir() else None}
    return None


def default_config(root: Path, slug: str, mode: str, wiki: dict | None, include_raw: bool) -> dict:
    cfg = {
        "engine_version": ENGINE_VERSION,
        "slug": slug,
        "mode": mode,
        "db_path": f"{DB_DIR_REL}/project.sqlite",
        "audit_path": f"{DB_DIR_REL}/audit.sqlite",
        "collections": [],
        "tabular": [],
        "exclude_keys": [],
        "query": {"row_limit": 200, "timeout_seconds": 5, "max_cell_chars": 400},
        "wiki": wiki or {},
        "d1": {"database_name": f"{slug}-db", "database_id": "", "worker_dir": f"{DB_DIR_REL}/worker"} if mode in ("d1", "both") else {},
        "ontology": {"gate": "warn"},
    }
    if wiki:
        cfg["collections"].append({"name": "wiki", "kind": "markdown", "root": wiki["root"], "glob": "**/*.md",
                                   "exclude": ["_schema/*", "_lint-report-*"], "type_field": "type", "scope_field": "client"})
        if include_raw:
            cfg["collections"].append({"name": "raw", "kind": "raw", "from": "sources"})
    return cfg


def append_wiki_log(root: Path, cfg: dict, title: str, body: str) -> bool:
    log_rel = cfg.get("wiki", {}).get("log")
    target = root / log_rel if log_rel else root / DB_DIR_REL / "LOG.md"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"---\ntype: log\nupdated: {now_iso()[:10]}\n---\n\n# project-db Operation Log\n\n", encoding="utf-8")
    text = target.read_text(encoding="utf-8")
    entry = f"\n## {now_iso()[:10]} — {title}\n\n{body.strip()}\n"
    text = text.rstrip("\n") + "\n" + entry
    m = FM_RE.match(text)
    if m and re.search(r"(?m)^updated:", m.group(1)):  # the log page's own `updated:` follows its newest entry
        text = text[:m.start(1)] + re.sub(r"(?m)^updated:.*$", f"updated: {now_iso()[:10]}", m.group(1), count=1) + text[m.end(1):]
    target.write_text(text, encoding="utf-8")
    # the log is itself a source (log_entries, and _log.md is a wiki page): fold the new entry in now,
    # otherwise the next session's hook reports "1 changed" for an edit the engine made itself
    if (root / cfg["db_path"]).exists():
        do_sync(root, cfg, full=False)
    return True


# ----------------------------------------------------------------------------- D1 export

D1_MAX_STMT = 90_000       # D1 hard limit is 100 KB per statement; keep headroom
D1_CHUNK = 60_000          # oversized text cells are appended in chunks with UPDATE … || …


def export_d1(root: Path, cfg: dict, out: Path) -> dict:
    conn = sqlite3.connect(f"file:{root / cfg['db_path']}?mode=ro", uri=True)
    lines: list[str] = ["-- project-db D1 import — generated " + now_iso() + " — no BEGIN/COMMIT (D1 batches are transactional)"]
    tables = [(n, s) for n, s in conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND sql NOT LIKE 'CREATE VIRTUAL%' AND name NOT LIKE '%_fts%' ORDER BY rowid")]
    views = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='view' ORDER BY rowid").fetchall()
    fts = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND sql LIKE 'CREATE VIRTUAL%'").fetchall()
    indexes = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall()
    for name, _ in views:
        lines.append(f'DROP VIEW IF EXISTS "{name}";')
    for name, _ in fts:
        lines.append(f'DROP TABLE IF EXISTS "{name}";')
    for name, _ in tables:
        lines.append(f'DROP TABLE IF EXISTS "{name}";')
    stats = {"tables": 0, "rows": 0, "statements": 0, "oversized_cells": 0}
    for name, ddl in tables:
        lines.append(ddl.replace("CREATE TABLE IF NOT EXISTS", "CREATE TABLE") + ";")
        cols = table_columns(conn, name)
        pk = "rowid"
        for r in conn.execute(f'PRAGMA table_info("{name}")'):
            if r[5] == 1 and r[2].upper() == "INTEGER":
                pk = r[1]
        prefix = f'INSERT INTO "{name}" ({", ".join(chr(34)+c+chr(34) for c in cols)}) VALUES '
        batch: list[str] = []
        size = len(prefix)
        deferred: list[str] = []
        for row in conn.execute(f'SELECT {pk if pk != "rowid" else "rowid"} AS __pk, * FROM "{name}"'):
            pkval, vals = row[0], list(row[1:])
            for i, v in enumerate(vals):
                if isinstance(v, str) and len(v.encode("utf-8")) > D1_CHUNK:
                    stats["oversized_cells"] += 1
                    b = v.encode("utf-8")
                    head, rest = b[:D1_CHUNK].decode("utf-8", errors="ignore"), b[D1_CHUNK:]
                    vals[i] = head
                    while rest:
                        piece, rest = rest[:D1_CHUNK].decode("utf-8", errors="ignore"), rest[D1_CHUNK:]
                        deferred.append(f'UPDATE "{name}" SET "{cols[i]}" = "{cols[i]}" || {sql_str(piece)} WHERE {pk} = {sql_str(pkval)};')
            tup = "(" + ", ".join(sql_str(v) for v in vals) + ")"
            if size + len(tup) + 2 > D1_MAX_STMT and batch:
                lines.append(prefix + ",\n".join(batch) + ";")
                stats["statements"] += 1
                batch, size = [], len(prefix)
            batch.append(tup)
            size += len(tup) + 2
            stats["rows"] += 1
        if batch:
            lines.append(prefix + ",\n".join(batch) + ";")
            stats["statements"] += 1
        lines.extend(deferred)
        stats["statements"] += len(deferred)
        stats["tables"] += 1
    for name, ddl in indexes:
        lines.append(ddl.replace("CREATE INDEX IF NOT EXISTS", "CREATE INDEX") + ";")
    for name, ddl in views:
        lines.append(ddl + ";")
    for name, ddl in fts:
        lines.append(ddl.replace("CREATE VIRTUAL TABLE IF NOT EXISTS", "CREATE VIRTUAL TABLE") + ";")
        lines.append(f'INSERT INTO "{name}"("{name}") VALUES (\'rebuild\');')
    lines.append("CREATE TABLE IF NOT EXISTS _query_log (id INTEGER PRIMARY KEY, ts TEXT NOT NULL, actor TEXT, tool TEXT, sql TEXT NOT NULL, rows INTEGER, ms INTEGER, truncated INTEGER NOT NULL DEFAULT 0, error TEXT);")
    conn.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines) + "\n"
    out.write_text(text, encoding="utf-8")
    stats["bytes"] = len(text.encode("utf-8"))
    stats["max_statement_bytes"] = max(len(s.encode("utf-8")) for s in lines)
    return stats


# ----------------------------------------------------------------------------- commands

def cmd_init(a):
    root = Path(a.root).resolve()
    skill_dir = Path(a.skill_dir).resolve() if a.skill_dir else Path(__file__).resolve().parent.parent
    wiki = None if a.no_wiki else detect_wiki(root)
    if a.wiki_root:
        w = root / a.wiki_root
        wiki = {"root": a.wiki_root, "log": f"{a.wiki_root}/_log.md" if (w / "_log.md").exists() else None,
                "templates": f"{a.wiki_root}/_schema/templates" if (w / "_schema" / "templates").is_dir() else None}
    slug = a.slug or ident(root.name).replace("_", "-")
    cfg_path = root / CONFIG_REL
    if cfg_path.exists() and not a.force:
        cfg = load_config(root)
        print(f"config exists at {CONFIG_REL} (slug={cfg.get('slug')}, mode={cfg.get('mode')}); re-installing + syncing. Use --force to rewrite config.")
    else:
        cfg = default_config(root, slug, a.mode, wiki, include_raw=not a.no_raw)
        for md in a.markdown or []:
            name, _, path = md.partition("=")
            cfg["collections"].append({"name": ident(name), "kind": "markdown", "root": path or name, "glob": "**/*.md", "exclude": [], "type_field": "type", "scope_field": "client", "default_type": ident(name).rstrip("s")})
        for tb in a.tabular or []:
            cfg["tabular"].append({"name": Path(tb).stem, "kind": Path(tb).suffix.lstrip(".").lower(), "path": tb, "table": ident(Path(tb).stem)})
        for k in a.exclude_key or []:
            cfg["exclude_keys"].append(k)
        save_config(root, cfg)
    report = install(root, cfg, skill_dir, has_wiki=bool(cfg.get("wiki")))
    stats = do_sync(root, cfg, full=True)
    counts = json.loads(get_state_ro(root, cfg, "counts") or "{}")
    body = (f"Mode `{cfg['mode']}`. Built `{cfg['db_path']}`: {counts.get('pages', 0)} pages "
            f"({', '.join(f'{n} {t}' for t, n in counts.get('by_type', {}).items())}), {counts.get('raw_documents', 0)} raw documents, "
            f"{len(stats['generated_views'])} typed views, {len(stats['curated_views_ok'])} curated views. "
            f"Installed: SessionStart hook (`{HOOK_REL}`), CLAUDE.md managed block, `.mcp.json` server, `.claude/db/SCHEMA.md`.")
    append_wiki_log(root, cfg, f"project-db init — queryable database for `{cfg['slug']}`", body)
    print(json.dumps({"config": CONFIG_REL, "install": report, "sync": stats, "counts": counts}, indent=1, default=str))
    if stats["curated_views_failed"]:
        print("warning: some curated views failed:\n  " + "\n  ".join(stats["curated_views_failed"]), file=sys.stderr)


def cmd_install(a):
    root = find_root(Path(a.root)) if a.root else find_root()
    cfg = load_config(root)
    skill_dir = Path(a.skill_dir).resolve() if a.skill_dir else Path(__file__).resolve().parent.parent
    print(json.dumps(install(root, cfg, skill_dir, has_wiki=bool(cfg.get("wiki"))), indent=1))


def cmd_sync(a):
    root = find_root(Path(a.root)) if a.root else find_root()
    cfg = load_config(root)
    stats = do_sync(root, cfg, full=a.full)
    n = stats["added"] + stats["changed"] + stats["removed"] + stats["raw_added"] + stats["raw_changed"] + stats["raw_removed"] + stats["tabular_reloaded"]
    if a.banner:
        print(banner(root, cfg, stats))
        if stats["curated_views_failed"]:
            print("  ⚠ curated views failed: " + "; ".join(stats["curated_views_failed"]))
        return
    ost = stats.get("ontology") or {}
    gate = ost.get("gate", "warn")
    if ost.get("present") and gate != "off" and (ost.get("strict") or ost.get("error")):
        what = ost.get("error") or f"{ost['strict']} strict ontology violation(s) — SELECT * FROM ontology_violations WHERE policy = 'strict'"
        print(f"{'error' if gate == 'fail' else 'warning'}: {what}", file=sys.stderr)
        if gate == "fail":
            sys.exit(3)
    if a.quiet and n == 0:
        return
    print(f"synced in {stats['seconds']}s — pages +{stats['added']} ~{stats['changed']} -{stats['removed']} · raw +{stats['raw_added']} ~{stats['raw_changed']} -{stats['raw_removed']} · tabular reloaded {stats['tabular_reloaded']} · views {len(stats['generated_views'])} typed + {len(stats['curated_views_ok'])} curated" + (" · FULL rebuild" if stats["full"] else ""))
    if stats["curated_views_failed"]:
        print("warning: curated views failed:\n  " + "\n  ".join(stats["curated_views_failed"]), file=sys.stderr)
    if a.full:
        append_wiki_log(root, cfg, "project-db full rebuild", f"Rebuilt `{cfg['db_path']}` — {json.loads(get_state_ro(root, cfg, 'counts') or '{}')}")


def cmd_query(a):
    root = find_root(Path(a.root)) if a.root else find_root()
    cfg = load_config(root)
    q = cfg.get("query", {})
    limit = q.get("row_limit", 200) if a.limit is None else a.limit
    timeout_s = q.get("timeout_seconds", 5) if a.timeout is None else a.timeout
    max_cell = q.get("max_cell_chars", 400) if a.max_cell is None else a.max_cell
    sql_text = a.sql if a.sql != "-" else sys.stdin.read()
    actor = a.actor or os.environ.get("PROJECT_DB_ACTOR") or os.environ.get("USER") or "unknown"
    session = os.environ.get("CLAUDE_SESSION_ID")
    target = "remote" if a.remote else "local"
    if a.remote and cfg.get("mode") == "local":
        die("this project is local-only; run /db:init --mode both to add D1")
    if not a.remote and cfg.get("mode") == "d1":
        target = "remote"
        a.remote = True
    rec = {"actor": actor, "session": session, "target": target, "sql": sql_text}
    try:
        sql = validate_sql(sql_text)
        if a.explain:
            sql = "EXPLAIN QUERY PLAN " + sql
        cols, rows, truncated, ms = run_query_remote(cfg, sql, limit) if a.remote else run_query_local(root, cfg, sql, limit, timeout_s)
    except (ValueError, TimeoutError, sqlite3.Error, RuntimeError) as e:
        rec["error"] = str(e)
        audit_write(root, cfg, rec)
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    rec.update({"rows": len(rows), "ms": ms, "truncated": truncated})
    audit_write(root, cfg, rec)
    print(format_rows(cols, rows, a.format, max_cell))
    note = f"# {len(rows)} row(s) · {ms} ms"
    if truncated:
        note += f" · TRUNCATED at {limit} rows — add WHERE / LIMIT, or --limit N"
    print(note, file=sys.stderr)


def cmd_schema(a):
    root = find_root(Path(a.root)) if a.root else find_root()
    cfg = load_config(root)
    conn = open_ro(root, cfg, 5)
    if a.object:
        obj = a.object
        row = conn.execute("SELECT type, sql FROM sqlite_master WHERE name=?", (obj,)).fetchone()
        if not row:
            die(f"no table or view named {obj}")
        docs = dict(conn.execute("SELECT column, doc FROM column_docs WHERE object=?", (obj,)).fetchall())
        n = conn.execute(f'SELECT COUNT(*) FROM "{obj}"').fetchone()[0]
        print(f"# {row[0]} {obj} — {n} rows" + (f" — {docs['_']}" if "_" in docs else ""))
        for r in conn.execute(f'PRAGMA table_info("{obj}")'):
            print(f"- {r[1]} {r[2] or ''}".rstrip() + (f" — {docs[r[1]]}" if r[1] in docs else ""))
        if a.full:
            print("\n```sql\n" + row[1] + "\n```")
        if a.sample:
            cols = table_columns(conn, obj)
            rows = conn.execute(f'SELECT * FROM "{obj}" LIMIT ?', (a.sample,)).fetchall()
            print("\n" + format_rows(cols, rows, "csv", 80))
    else:
        md = get_state(conn, "schema_md") or schema_markdown(conn, cfg, root)
        print(md)
    conn.close()


def cmd_search(a):
    root = find_root(Path(a.root)) if a.root else find_root()
    cfg = load_config(root)
    conn = open_ro(root, cfg, 5)
    try:
        cols, rows = fts_search(conn, a.terms, a.type, a.limit, a.raw)
    except sqlite3.OperationalError as e:
        die(f"FTS query error: {e} — quote phrases, e.g. \"budget management\"")
    finally:
        conn.close()
    print(format_rows(cols, rows, a.format, 300))
    print(f"# {len(rows)} hit(s)", file=sys.stderr)


def cmd_status(a):
    root = find_root(Path(a.root)) if a.root else find_root()
    cfg = load_config(root)
    db_path = root / cfg["db_path"]
    if not db_path.exists():
        print("database not built — run /db:sync")
        return
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    counts = json.loads(get_state(conn, "counts") or "{}")
    info = {
        "slug": cfg.get("slug"), "mode": cfg.get("mode"), "db": cfg["db_path"], "size_mb": round(db_path.stat().st_size / 1e6, 2),
        "engine": get_state(conn, "engine_version"), "last_sync": get_state(conn, "last_sync"), "last_build": get_state(conn, "last_build"),
        "last_publish": get_state(conn, "last_publish"), "counts": counts,
        "typed_views": json.loads(get_state(conn, "generated_views") or "[]"), "curated_views": json.loads(get_state(conn, "curated_views") or "[]"),
        "fts": fts_available(conn), "collections": [c["name"] for c in cfg.get("collections", [])], "tabular": [t["name"] for t in cfg.get("tabular", [])],
    }
    conn.close()
    apath = root / cfg.get("audit_path", f"{DB_DIR_REL}/audit.sqlite")
    if apath.exists():
        ac = sqlite3.connect(f"file:{apath}?mode=ro", uri=True)
        try:
            info["queries_logged"] = ac.execute("SELECT COUNT(*) FROM query_log").fetchone()[0]
            info["query_errors"] = ac.execute("SELECT COUNT(*) FROM query_log WHERE error IS NOT NULL").fetchone()[0]
        except sqlite3.Error:
            pass
        ac.close()
    print(json.dumps(info, indent=1))


def cmd_audit(a):
    root = find_root(Path(a.root)) if a.root else find_root()
    cfg = load_config(root)
    apath = root / cfg.get("audit_path", f"{DB_DIR_REL}/audit.sqlite")
    if not apath.exists():
        print("no queries logged yet")
        return
    conn = sqlite3.connect(f"file:{apath}?mode=ro", uri=True)
    if a.errors:
        rows = conn.execute("SELECT ts, actor, error, sql FROM query_log WHERE error IS NOT NULL ORDER BY id DESC LIMIT ?", (a.tail,)).fetchall()
        print(format_rows(["ts", "actor", "error", "sql"], rows, "csv", 300))
    elif a.top:
        rows = conn.execute("SELECT COUNT(*) AS n, ROUND(AVG(ms)) AS avg_ms, sql FROM query_log WHERE error IS NULL GROUP BY sql ORDER BY n DESC LIMIT ?", (a.tail,)).fetchall()
        print(format_rows(["n", "avg_ms", "sql"], rows, "csv", 300))
        print("# repeated queries are view candidates for .claude/db/views.sql", file=sys.stderr)
    else:
        rows = conn.execute("SELECT ts, actor, target, rows, ms, truncated, COALESCE(error,'') AS error, sql FROM query_log ORDER BY id DESC LIMIT ?", (a.tail,)).fetchall()
        print(format_rows(["ts", "actor", "target", "rows", "ms", "truncated", "error", "sql"], rows, "csv", 200))
    conn.close()


def cmd_export_d1(a):
    root = find_root(Path(a.root)) if a.root else find_root()
    cfg = load_config(root)
    out = Path(a.out) if a.out else root / DB_DIR_REL / "d1" / "import.sql"
    stats = export_d1(root, cfg, out)
    stats["out"] = str(out)
    if stats["max_statement_bytes"] > 100_000:
        stats["warning"] = "a statement exceeds D1's 100 KB limit"
    if stats["bytes"] > 500 * 1024 * 1024:
        stats["warning"] = "import exceeds the D1 free-tier 500 MB database limit"
    print(json.dumps(stats, indent=1))


def cmd_publish_record(a):
    """Stamp last_publish + D1 settings after a successful /db:publish, and log it. The publish itself is
    a runbook of wrangler calls (references/d1-publish.md); this is the bookkeeping that makes
    `status`, the banner and the log agree on what was published when."""
    root = find_root(Path(a.root)) if a.root else find_root()
    cfg = load_config(root)
    d1 = cfg.setdefault("d1", {})
    if a.database:
        d1["database_name"] = a.database
    if a.database_id:
        d1["database_id"] = a.database_id
    if a.url:
        d1["worker_url"] = a.url
    save_config(root, cfg)
    conn = open_rw(root, cfg)
    with conn:
        set_state(conn, "last_publish", now_iso())
        counts = json.loads(get_state(conn, "counts") or "{}")
    conn.close()
    body = (f"Published `{cfg['db_path']}` to D1 `{d1.get('database_name', '?')}`"
            + (f" (id `{d1['database_id']}`)" if d1.get("database_id") else "")
            + f": {counts.get('pages', 0)} pages, {counts.get('raw_documents', 0)} raw documents."
            + (f" MCP Worker: {d1['worker_url']}/mcp" if d1.get("worker_url") else ""))
    append_wiki_log(root, cfg, f"project-db publish — {d1.get('database_name', '?')}", body)
    print(json.dumps({"last_publish": now_iso(), "d1": d1}, indent=1))


def cmd_verify(a):
    root = find_root(Path(a.root)) if a.root else find_root()
    cfg = load_config(root)
    results = []

    def check(name, ok, detail=""):
        results.append((name, ok, detail))

    db_path = root / cfg["db_path"]
    check("database file exists", db_path.exists(), str(db_path))
    if not db_path.exists():
        _print_checks(results)
        sys.exit(1)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    for coll in cfg.get("collections", []):
        if coll.get("kind") != "markdown":
            continue
        files = sum(1 for _ in iter_collection_files(root, coll))
        rows = conn.execute("SELECT COUNT(*) FROM pages WHERE collection=?", (coll["name"],)).fetchone()[0]
        check(f"collection '{coll['name']}' row count matches files", files == rows, f"{rows} rows / {files} files")
    for (v,) in conn.execute("SELECT name FROM sqlite_master WHERE type='view'"):
        try:
            conn.execute(f'SELECT * FROM "{v}" LIMIT 1').fetchall()
            check(f"view {v} compiles", True)
        except sqlite3.Error as e:
            check(f"view {v} compiles", False, str(e))
    if fts_available(conn):
        try:
            n = conn.execute("SELECT COUNT(*) FROM pages_fts").fetchone()[0]
            check("FTS index populated", n == conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0], f"{n} indexed")
        except sqlite3.Error as e:
            check("FTS index populated", False, str(e))
    unresolved = conn.execute("SELECT COUNT(*) FROM links WHERE to_id IS NULL").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    check("links resolved (info)", True, f"{total - unresolved}/{total} resolved; {unresolved} broken → SELECT * FROM broken_links")
    conn.close()
    # read-only enforcement — try to write through the guarded path
    try:
        validate_sql("DELETE FROM pages")
        check("validator rejects writes", False, "DELETE passed validation")
    except ValueError:
        check("validator rejects writes", True)
    try:
        ro = open_ro(root, cfg, 2)
        ro.execute("CREATE TEMP TABLE x(a)")
        check("authorizer denies DDL", False)
    except sqlite3.DatabaseError:
        check("authorizer denies DDL", True)
    try:
        ro = open_ro(root, cfg, 2)
        ro.execute("SELECT 1").fetchall()
        check("read-only connection works", True)
    except sqlite3.Error as e:
        check("read-only connection works", False, str(e))
    check("SCHEMA.md written", (root / DB_DIR_REL / "SCHEMA.md").exists())
    check("SessionStart hook installed", (root / HOOK_REL).exists() and "db-context.sh" in ((root / ".claude/settings.json").read_text() if (root / ".claude/settings.json").exists() else ""))
    cm = root / "CLAUDE.md"
    check("CLAUDE.md managed block present", cm.exists() and SENTINEL_OPEN in cm.read_text(encoding="utf-8"))
    check(".mcp.json registers project-db", (root / ".mcp.json").exists() and "project-db" in (root / ".mcp.json").read_text())
    ost = json.loads(get_state_ro(root, cfg, "ontology") or "{}")
    if (root / ONTOLOGY_ENGINE_REL).exists():
        check("ontology loaded into the database", bool(ost.get("present")) and not ost.get("error"), ost.get("error") or f"{ost.get('terms', 0)} terms")
        if ost.get("present") and not ost.get("error"):
            fail_gate = (cfg.get("ontology") or {}).get("gate", "warn") == "fail"
            check("ontology strict violations = 0" + ("" if fail_gate else " (info: gate is warn)"), (ost.get("strict", 0) == 0) or not fail_gate,
                  f"{ost.get('strict', 0)} strict · {ost.get('warn', 0)} warn → SELECT * FROM ontology_violations")
    _print_checks(results)
    sys.exit(0 if all(ok for _, ok, _ in results) else 1)


def _print_checks(results):
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    n_ok = sum(1 for _, ok, _ in results if ok)
    print(f"# {n_ok}/{len(results)} checks passed")


def main(argv=None):
    p = argparse.ArgumentParser(prog="db.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create config, install hook/mandate/MCP, full build")
    s.add_argument("--root", default=".")
    s.add_argument("--slug")
    s.add_argument("--mode", choices=["local", "d1", "both"], default="local")
    s.add_argument("--skill-dir", help="path to skills/project-db (templates live there)")
    s.add_argument("--wiki-root", help="wiki vault directory relative to root (auto-detected)")
    s.add_argument("--no-wiki", action="store_true", help="do not treat any directory as a wiki")
    s.add_argument("--no-raw", action="store_true", help="do not load raw documents cited in sources:")
    s.add_argument("--markdown", action="append", metavar="NAME=DIR", help="extra markdown collection (no-wiki projects), e.g. adr=docs/adr")
    s.add_argument("--tabular", action="append", metavar="PATH", help="CSV/JSON/JSONL file to load as its own table")
    s.add_argument("--exclude-key", action="append", help="frontmatter key never loaded (PII etc.)")
    s.add_argument("--force", action="store_true", help="rewrite an existing config")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("install", help="re-vendor templates + merge CLAUDE.md / settings / .mcp.json")
    s.add_argument("--root")
    s.add_argument("--skill-dir")
    s.set_defaults(fn=cmd_install)

    s = sub.add_parser("sync", help="incremental sync")
    s.add_argument("--root")
    s.add_argument("--full", action="store_true", help="drop and rebuild everything")
    s.add_argument("--quiet", action="store_true", help="print nothing when nothing changed")
    s.add_argument("--banner", action="store_true", help="print the SessionStart banner after syncing")
    s.set_defaults(fn=cmd_sync)

    s = sub.add_parser("build", help="full rebuild (alias for sync --full)")
    s.add_argument("--root")
    s.set_defaults(fn=lambda a: cmd_sync(argparse.Namespace(root=a.root, full=True, quiet=False, banner=False)))

    s = sub.add_parser("query", help="run one read-only statement")
    s.add_argument("sql", help="SQL text, or - to read from stdin")
    s.add_argument("--root")
    s.add_argument("--format", choices=["csv", "json", "md"], default="csv")
    s.add_argument("--limit", type=int, help="row cap (0 = none)")
    s.add_argument("--timeout", type=float, help="seconds")
    s.add_argument("--max-cell", type=int, help="truncate cells longer than N chars (0 = never)")
    s.add_argument("--remote", action="store_true", help="run against D1 via wrangler instead of the local file")
    s.add_argument("--explain", action="store_true", help="prefix EXPLAIN QUERY PLAN")
    s.add_argument("--actor", help="who is asking (audit log); default $PROJECT_DB_ACTOR or $USER")
    s.set_defaults(fn=cmd_query)

    s = sub.add_parser("schema", help="agent-facing schema summary")
    s.add_argument("object", nargs="?", help="table or view name for column detail")
    s.add_argument("--root")
    s.add_argument("--full", action="store_true", help="include the CREATE statement")
    s.add_argument("--sample", type=int, default=0, help="show N sample rows (cells cut at 80 chars)")
    s.set_defaults(fn=cmd_schema)

    s = sub.add_parser("search", help="full-text search")
    s.add_argument("terms")
    s.add_argument("--root")
    s.add_argument("--type")
    s.add_argument("--raw", action="store_true", help="also search raw documents")
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--format", choices=["csv", "json", "md"], default="csv")
    s.set_defaults(fn=cmd_search)

    s = sub.add_parser("status", help="freshness + counts")
    s.add_argument("--root")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("audit", help="recent queries from the audit log")
    s.add_argument("--root")
    s.add_argument("--tail", type=int, default=20)
    s.add_argument("--errors", action="store_true", help="only failed queries")
    s.add_argument("--top", action="store_true", help="most repeated queries (view candidates)")
    s.set_defaults(fn=cmd_audit)

    s = sub.add_parser("export-d1", help="write a D1-safe import.sql")
    s.add_argument("--root")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_export_d1)

    s = sub.add_parser("publish-record", help="record a completed D1 publish (last_publish, database id, worker url) and log it")
    s.add_argument("--root")
    s.add_argument("--database", help="D1 database name")
    s.add_argument("--database-id", help="D1 database id (from wrangler d1 create)")
    s.add_argument("--url", help="deployed Worker base URL")
    s.set_defaults(fn=cmd_publish_record)

    s = sub.add_parser("verify", help="integrity + guardrail checks")
    s.add_argument("--root")
    s.set_defaults(fn=cmd_verify)

    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
