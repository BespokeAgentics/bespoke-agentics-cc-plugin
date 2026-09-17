# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=2,<3"]
# ///
"""project-db — local stdio MCP server over the project's SQLite database.

Installed at .claude/db/mcp_server.py and registered in .mcp.json as:
    uv run --quiet .claude/db/mcp_server.py

It is a thin shell around db.py: the same validator, read-only authorizer, timeout, row cap, cell
truncation and audit log apply, so an MCP client (Claude Desktop, Cursor, another agent) gets exactly
the guardrails the CLI has. Nothing here can write to the database.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db as engine  # noqa: E402

from mcp.server.mcpserver import MCPServer  # noqa: E402

ROOT = engine.find_root(Path.cwd()) if (Path.cwd() / engine.CONFIG_REL).exists() else engine.find_root(Path(__file__).resolve().parent)
CFG = engine.load_config(ROOT)
QCFG = CFG.get("query", {})

server = MCPServer("project-db")


def _actor() -> str:
    return os.environ.get("PROJECT_DB_ACTOR") or "mcp"


@server.tool()
def db_query(sql: str, limit: int = 0, format: str = "csv", max_cell: int = -1) -> str:
    """Run ONE read-only SQL statement (SELECT / WITH … SELECT / EXPLAIN QUERY PLAN) against the project
    database and return CSV (default), json, or md. Read `db_schema` first. Rows are capped (default from
    config, usually 200) and long cells are truncated; narrow the query with WHERE / LIMIT rather than
    raising caps. Every call is audited."""
    lim = QCFG.get("row_limit", 200) if not limit else limit
    mc = QCFG.get("max_cell_chars", 400) if max_cell < 0 else max_cell
    rec = {"actor": _actor(), "session": os.environ.get("CLAUDE_SESSION_ID"), "target": "local", "sql": sql}
    try:
        stmt = engine.validate_sql(sql)
        cols, rows, truncated, ms = engine.run_query_local(ROOT, CFG, stmt, lim, QCFG.get("timeout_seconds", 5))
    except Exception as e:  # surface the reason to the caller; it is the self-correction loop
        rec["error"] = str(e)
        engine.audit_write(ROOT, CFG, rec)
        return f"error: {e}"
    rec.update({"rows": len(rows), "ms": ms, "truncated": truncated})
    engine.audit_write(ROOT, CFG, rec)
    out = engine.format_rows(cols, rows, format if format in ("csv", "json", "md") else "csv", mc)
    note = f"\n# {len(rows)} row(s) · {ms} ms"
    if truncated:
        note += f" · TRUNCATED at {lim} rows — add WHERE / LIMIT"
    return out + note


@server.tool()
def db_schema(object: str = "") -> str:
    """Schema summary for the project database (tables, typed views, curated views, column docs, query
    patterns). Pass a table/view name for its columns and docs. Read this before writing SQL."""
    conn = engine.open_ro(ROOT, CFG, 5)
    try:
        if not object:
            return engine.get_state(conn, "schema_md") or engine.schema_markdown(conn, CFG, ROOT)
        row = conn.execute("SELECT type FROM sqlite_master WHERE name=?", (object,)).fetchone()
        if not row:
            return f"error: no table or view named {object}"
        docs = dict(conn.execute("SELECT column, doc FROM column_docs WHERE object=?", (object,)).fetchall())
        n = conn.execute(f'SELECT COUNT(*) FROM "{object}"').fetchone()[0]
        lines = [f"# {row[0]} {object} — {n} rows" + (f" — {docs['_']}" if "_" in docs else "")]
        for r in conn.execute(f'PRAGMA table_info("{object}")'):
            lines.append(f"- {r[1]} {r[2] or ''}".rstrip() + (f" — {docs[r[1]]}" if r[1] in docs else ""))
        return "\n".join(lines)
    except Exception as e:  # an MCP tool must return the reason, not crash the server
        return f"error: {e}"
    finally:
        conn.close()


@server.tool()
def db_search(terms: str, type: str = "", limit: int = 20, include_raw: bool = False) -> str:
    """Full-text search (FTS5) over page titles and bodies; returns slug, type, client and a snippet.
    Use FTS syntax: `budget AND approval`, `"co-op billing"`, `warehouse*`. Then query the page by slug."""
    try:
        conn = engine.open_ro(ROOT, CFG, 5)
    except SystemExit:
        return "error: database not built yet — run /db:sync"
    try:
        cols, rows = engine.fts_search(conn, terms, type or None, limit, include_raw)
    except Exception as e:
        return f"error: {e} — quote phrases, e.g. \"co-op billing\""
    finally:
        conn.close()
    return engine.format_rows(cols, rows, "csv", 300) + f"\n# {len(rows)} hit(s)"


@server.tool()
def db_status() -> str:
    """Freshness and counts: last sync, pages by type, raw documents, views, mode (local / d1 / both)."""
    import json
    try:
        conn = engine.open_ro(ROOT, CFG, 5)
    except SystemExit:
        return "error: database not built yet — run /db:sync"
    try:
        return json.dumps({
            "slug": CFG.get("slug"), "mode": CFG.get("mode"), "engine": engine.ENGINE_VERSION,
            "last_sync": engine.get_state(conn, "last_sync"), "last_publish": engine.get_state(conn, "last_publish"),
            "counts": json.loads(engine.get_state(conn, "counts") or "{}"),
            "typed_views": json.loads(engine.get_state(conn, "generated_views") or "[]"),
            "curated_views": json.loads(engine.get_state(conn, "curated_views") or "[]"),
        }, indent=1)
    except Exception as e:
        return f"error: {e}"
    finally:
        conn.close()


if __name__ == "__main__":
    server.run()
