#!/usr/bin/env python3
"""Regression tests for the project-db engine. Stdlib only.

Run from anywhere:  python3 <skill>/scripts/test_db.py
Each test builds a throwaway project in a temp dir, so nothing here touches a real wiki.

Every test names the defect or behaviour it pins. Two of them (curated-view docs, tabular docs on
incremental sync) were found by eval agents against v1.0.0 and must never come back.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import db as engine  # noqa: E402

SKILL_DIR = HERE.parent


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


PAGE = """---
type: {type}
client: acme
status: {status}
severity: {severity}
related-feature: "[[feature|{feature}]]"
tags: [alpha, beta]
sources: [raw/notes.md]
---

# {title}

## Overview
Body mentions [[{link}]] and [[Missing Page]].
<!-- template guidance: link to [[feature|Features]] -->

## Current State
Second section text.
"""


class Project:
    """A tiny vault + init, torn down after each test."""

    def __init__(self, with_templates: bool = True):
        self.root = Path(tempfile.mkdtemp(prefix="project-db-test-"))
        wiki = self.root / "wiki"
        write(wiki / "_index.md", "---\ntype: index\n---\n# Index\n")
        write(wiki / "_log.md", "---\ntype: log\n---\n# Log\n\n## 2026-01-01 — created\n\nfirst entry\n")
        if with_templates:
            write(wiki / "_schema" / "SCHEMA.md", "# schema\n\nExample link: [[Budget Management]] and CREATE VIEW nothing.\n")
            write(wiki / "_schema" / "templates" / "gap.md", "---\ntype: gap\nclient:\nstatus: # open|mitigated|resolved\nseverity: # critical|high|medium|low\nrelated-feature:\ncreated:\nupdated:\nsources:\ntags:\n---\n# Gap\n")
        write(wiki / "clients" / "acme" / "gaps" / "gap-one.md", PAGE.format(type="gap", status="open", severity="critical", feature="feat-one", title="Gap One", link="feat-one"))
        write(wiki / "clients" / "acme" / "gaps" / "gap-two.md", PAGE.format(type="gap", status="resolved", severity="low", feature="feat-one", title="Gap Two", link="Feature One"))
        write(wiki / "clients" / "acme" / "features" / "feat-one.md", "---\ntype: feature\nclient: acme\nstatus: active\n---\n# Feature One\n\nSee [[acme]].\n")
        write(wiki / "platforms" / "acme" / "overview.md", "---\ntype: platform\n---\n# Acme platform\n")
        write(self.root / "raw" / "notes.md", "# Notes\n\nraw transcript text about budgets\n")
        write(self.root / "data" / "people.csv", "id,name,score\n1,Ann,10\n2,Bob,20\n")
        write(self.root / "CLAUDE.md", "# Existing\n\nkeep me\n")

    def init(self, *extra: str) -> None:
        engine.main(["init", "--root", str(self.root), "--slug", "t", "--mode", "local", "--skill-dir", str(SKILL_DIR), *extra])

    def q(self, sql: str, *params):
        conn = sqlite3.connect(f"file:{self.root / '.claude/db/project.sqlite'}?mode=ro", uri=True)
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


class Quiet:
    """Silence engine stdout inside tests."""

    def __enter__(self):
        self._out, sys.stdout = sys.stdout, open(os.devnull, "w")
        return self

    def __exit__(self, *a):
        sys.stdout.close()
        sys.stdout = self._out


class ParsingTests(unittest.TestCase):
    def test_frontmatter_subset(self):
        data, docs = engine.parse_yaml_subset('a: 1\nb: [x, "y z", [[link]]]\nc: # open|closed\nd:\n  - one\n  - two\ne: "quoted # not a comment"\nf: true')
        self.assertEqual(data["a"], 1)
        self.assertEqual(data["b"], ["x", "y z", "[[link]]"])
        self.assertIsNone(data["c"])
        self.assertEqual(docs["c"], "open|closed")
        self.assertEqual(data["d"], ["one", "two"])
        self.assertEqual(data["e"], "quoted # not a comment")
        self.assertIs(data["f"], True)

    def test_links_ignore_html_comments_and_capture_labels(self):
        parsed = engine.parse_page(PAGE.format(type="gap", status="open", severity="high", feature="f", title="T", link="target"), "x/t.md")
        targets = {(t, k) for t, _, k, _ in parsed["links"]}
        self.assertIn(("target", "body"), targets)
        self.assertIn(("Missing Page", "body"), targets)
        self.assertIn(("feature", "frontmatter:related-feature"), targets)
        self.assertNotIn(("feature", "body"), targets, "a link inside <!-- --> is not a link")
        self.assertEqual(parsed["title"], "T")
        self.assertEqual([s[2] for s in parsed["sections"]], ["T", "Overview", "Current State"])  # the H1 is section 0

    def test_view_doc_ignores_header_prose(self):
        # the views.sql header rides along with the first statement and mentions `-- doc:` in prose
        stmt = "-- header: the `-- doc:` line inside each statement becomes the description\n-- and every CREATE VIEW below is recreated\nCREATE VIEW v AS\n  -- doc: the real doc\n  SELECT 1"
        self.assertEqual(engine.view_doc(stmt), "the real doc")
        self.assertIsNone(engine.view_doc("CREATE VIEW v AS SELECT 1"))

    def test_split_sql_respects_strings_and_comments(self):
        stmts = engine.split_sql("SELECT 'a;b'; -- c;d\nSELECT 2 /* ; */; ")
        self.assertEqual(len(stmts), 2)

    def test_fts_terms_quotes_punctuation_only_when_user_wrote_no_syntax(self):
        self.assertEqual(engine.fts_terms("co-op billing"), '"co-op" "billing"')
        self.assertEqual(engine.fts_terms("budget AND approval"), "budget AND approval")
        self.assertEqual(engine.fts_terms('"co-op billing"'), '"co-op billing"')
        self.assertEqual(engine.fts_terms("budget approval"), "budget approval")


class GuardrailTests(unittest.TestCase):
    def test_validator(self):
        self.assertEqual(engine.validate_sql("SELECT 1;"), "SELECT 1")
        for bad in ["SELECT 1; SELECT 2", "UPDATE pages SET title='x'", "WITH t AS (SELECT 1) INSERT INTO tags SELECT 1,'x'",
                    "PRAGMA writable_schema=1", "ATTACH 'x' AS y", "DELETE FROM pages"]:
            with self.assertRaises(ValueError, msg=bad):
                engine.validate_sql(bad)
        self.assertTrue(engine.validate_sql("WITH t AS (SELECT replace('a','a','b') AS r) SELECT r FROM t").startswith("WITH"))

    def test_authorizer_denies_writes_and_allows_fts_pragmas(self):
        self.assertEqual(engine._authorizer(sqlite3.SQLITE_INSERT, "pages", None, "main", None), sqlite3.SQLITE_DENY)
        self.assertEqual(engine._authorizer(sqlite3.SQLITE_PRAGMA, "writable_schema", None, "main", None), sqlite3.SQLITE_DENY)
        self.assertEqual(engine._authorizer(sqlite3.SQLITE_PRAGMA, "data_version", None, "main", None), sqlite3.SQLITE_OK)
        self.assertEqual(engine._authorizer(sqlite3.SQLITE_SELECT, None, None, None, None), sqlite3.SQLITE_OK)


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.p = Project()
        with Quiet():
            self.p.init("--tabular", "data/people.csv")

    def tearDown(self):
        self.p.cleanup()

    def test_init_builds_everything(self):
        self.assertEqual(self.p.q("SELECT COUNT(*) FROM pages")[0][0], 6)  # _index, _log, 2 gaps, feature, platform overview (SCHEMA.md + templates excluded)
        views = {r[0] for r in self.p.q("SELECT name FROM sqlite_master WHERE type='view'")}
        self.assertIn("gaps", views)
        self.assertIn("features", views)
        self.assertNotIn("indexes", views, "index/log types get no typed view")
        self.assertIn("backlinks", views)
        cols = [r[1] for r in self.p.q("PRAGMA table_info(gaps)")]
        self.assertIn("severity", cols)
        self.assertIn("related_feature", cols)
        self.assertIn("frontmatter", cols, "typed views keep frontmatter so json_extract keeps working")
        self.assertEqual(self.p.q("SELECT doc FROM column_docs WHERE object='gaps' AND column='severity'")[0][0], "critical|high|medium|low")
        self.assertEqual(self.p.q("SELECT doc FROM column_docs WHERE object='backlinks' AND column='_'")[0][0][:14], "who links TO a")
        self.assertEqual(self.p.q("SELECT COUNT(*) FROM raw_documents")[0][0], 1, "cited raw file loaded")
        self.assertEqual(self.p.q("SELECT COUNT(*) FROM people")[0][0], 2)
        self.assertEqual(self.p.q("SELECT typeof(score) FROM people LIMIT 1")[0][0], "integer")
        for rel in [".claude/db/db.py", ".claude/db/SCHEMA.md", ".claude/db/views.sql", ".claude/db/mcp_server.py", ".claude/hooks/db-context.sh", ".claude/settings.json", ".mcp.json"]:
            self.assertTrue((self.p.root / rel).exists(), rel)
        claude = (self.p.root / "CLAUDE.md").read_text()
        self.assertIn("keep me", claude)
        self.assertIn(engine.SENTINEL_OPEN, claude)
        self.assertIn("query layer over the wiki", claude)
        self.assertIn("db-context.sh", json.loads((self.p.root / ".claude/settings.json").read_text())["hooks"]["SessionStart"][0]["hooks"][0]["command"])

    def test_link_resolution_rules(self):
        rows = {(r[0], r[1]): r[2] for r in self.p.q("SELECT l.to_slug, l.match, l.to_id IS NOT NULL FROM links l")}
        self.assertEqual(rows[("feat-one", "slug")], 1)
        self.assertEqual(rows[("Feature One", "title")], 1)
        self.assertEqual(rows[("feature", "label")], 1, "[[feature|feat-one]] resolves through the label")
        self.assertEqual(rows[("acme", "folder")], 1, "[[acme]] resolves to platforms/acme/overview.md")
        self.assertEqual(rows[("Missing Page", None)], 0)

    def test_incremental_sync_add_change_delete_and_quiet(self):
        gaps = self.p.root / "wiki/clients/acme/gaps"
        (gaps / "gap-one.md").write_text((gaps / "gap-one.md").read_text().replace("severity: critical", "severity: medium"))
        write(gaps / "gap-three.md", PAGE.format(type="gap", status="open", severity="high", feature="feat-one", title="Gap Three", link="feat-one"))
        (gaps / "gap-two.md").unlink()
        cfg = engine.load_config(self.p.root)
        stats = engine.do_sync(self.p.root, cfg, full=False)
        self.assertEqual((stats["added"], stats["changed"], stats["removed"]), (1, 1, 1))
        self.assertEqual(self.p.q("SELECT severity FROM gaps WHERE slug='gap-one'")[0][0], "medium")
        self.assertEqual(self.p.q("SELECT COUNT(*) FROM pages WHERE slug='gap-two'")[0][0], 0)
        stats = engine.do_sync(self.p.root, cfg, full=False)
        self.assertEqual(stats["added"] + stats["changed"] + stats["removed"], 0)

    def test_tabular_docs_republish_on_incremental_sync(self):
        cfg = engine.load_config(self.p.root)
        cfg["tabular"][0]["doc"] = "people export"
        cfg["tabular"][0]["column_docs"] = {"score": "0-100"}
        engine.save_config(self.p.root, cfg)
        engine.do_sync(self.p.root, cfg, full=False)  # data unchanged → hash short-circuit path
        self.assertEqual(self.p.q("SELECT doc FROM column_docs WHERE object='people' AND column='_'")[0][0], "people export")
        self.assertEqual(self.p.q("SELECT doc FROM column_docs WHERE object='people' AND column='score'")[0][0], "0-100")
        self.assertIn("people export", (self.p.root / ".claude/db/SCHEMA.md").read_text())

    def test_query_guardrails_end_to_end(self):
        cfg = engine.load_config(self.p.root)
        cols, rows, truncated, _ = engine.run_query_local(self.p.root, cfg, "SELECT slug FROM pages ORDER BY slug", 2, 5)
        self.assertEqual((len(rows), truncated), (2, True))
        with self.assertRaises(sqlite3.DatabaseError):
            engine.run_query_local(self.p.root, cfg, "CREATE TEMP TABLE x(a)", 10, 5)
        with self.assertRaises(TimeoutError):
            engine.run_query_local(self.p.root, cfg, "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c) SELECT COUNT(*) FROM c", 10, 0.2)
        conn = engine.open_ro(self.p.root, cfg, 5)
        try:
            cols, rows = engine.fts_search(conn, "budgets", None, 10, True)
            self.assertTrue(any(r[1] == "raw:md" for r in rows), "raw documents are searchable with --raw")
        finally:
            conn.close()

    def test_export_d1_has_no_transactions_and_small_statements(self):
        cfg = engine.load_config(self.p.root)
        out = self.p.root / "import.sql"
        stats = engine.export_d1(self.p.root, cfg, out)
        text = out.read_text()
        self.assertNotIn("BEGIN TRANSACTION", text)
        self.assertNotIn("COMMIT;", text)
        self.assertLess(stats["max_statement_bytes"], 100_000)
        self.assertIn("INSERT INTO \"pages_fts\"(\"pages_fts\") VALUES ('rebuild');", text)

    def test_install_is_idempotent(self):
        cfg = engine.load_config(self.p.root)
        before = (self.p.root / "CLAUDE.md").read_text()
        with Quiet():
            report = engine.install(self.p.root, cfg, SKILL_DIR, has_wiki=True)
        self.assertEqual(report.get("CLAUDE.md"), "unchanged")
        self.assertEqual((self.p.root / "CLAUDE.md").read_text(), before)
        self.assertEqual(len(json.loads((self.p.root / ".claude/settings.json").read_text())["hooks"]["SessionStart"]), 1)


class DeterminismTests(unittest.TestCase):
    def test_parse_never_depends_on_pyyaml(self):
        """With PyYAML installed, `related: [[Page]]` became a nested list and its link vanished — the same
        wiki indexed differently on two machines. The subset parser is now the only parser."""
        import types
        fake = types.ModuleType("yaml")
        fake.safe_load = lambda text: {"poisoned": True}
        saved = sys.modules.get("yaml")
        sys.modules["yaml"] = fake
        try:
            data, _ = engine.parse_yaml_subset("related: [[Page One]]\ntags:\n- a\n- b")
        finally:
            if saved is None:
                del sys.modules["yaml"]
            else:
                sys.modules["yaml"] = saved
        self.assertEqual(data, {"related": "[[Page One]]", "tags": ["a", "b"]})

    def test_links_inside_code_are_not_links(self):
        page = engine.parse_page("# T\n\nreal [[a]]\n\n```\n[[in-fence]]\n```\n\nand `[[inline]]` and <!-- [[comment]] -->\n", "t.md")
        self.assertEqual([l[0] for l in page["links"]], ["a"])


ONTOLOGY_SKILL = SKILL_DIR.parent / "project-ontology"


class OntologyIntegrationTests(unittest.TestCase):
    """Acceptance: `SELECT * FROM ontology_violations` is empty on a clean vault and non-empty after a
    planted error — computed by the vendored project-ontology engine, the same rules as the write hook."""

    def setUp(self):
        if not (ONTOLOGY_SKILL / "scripts" / "ontology.py").exists():
            self.skipTest("project-ontology skill not present")
        import importlib.util
        spec = importlib.util.spec_from_file_location("ontology_engine_for_tests", ONTOLOGY_SKILL / "scripts" / "ontology.py")
        self.onto = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.onto)
        self.root = Path(tempfile.mkdtemp(prefix="project-db-ontology-"))
        w = self.root / "wiki"
        write(w / "_index.md", "---\ntype: index\n---\n# Index\n\n[[gap-a]]\n")
        write(w / "_log.md", "---\ntype: log\n---\n# Log\n")
        write(w / "_schema" / "SCHEMA.md", "# Schema\n")
        write(w / "_schema" / "templates" / "gap.md", "---\ntype: gap\nclient:\nstatus: # open|resolved\nseverity: # critical|high|low\ntags:\n---\n# Gap\n")
        write(w / "clients" / "acme" / "README.md", "# Acme\n")
        write(w / "clients" / "acme" / "gaps" / "gap-a.md", "---\ntype: gap\nclient: acme\nstatus: open\nseverity: high\ntags: [billing]\n---\n# Gap A\n\nSee [[gap-b]].\n")
        write(w / "clients" / "acme" / "gaps" / "gap-b.md", "---\ntype: gap\nclient: acme\nstatus: resolved\nseverity: low\n---\n# Gap B\n\nOwned by acme. See [[gap-a]].\n")
        decisions = self.root / "decisions.json"
        decisions.write_text(json.dumps({"approve": ["*"], "aliases": {"client.acme": ["Acme Corp"]}}))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.onto.main(["init", "--scan", "--root", str(self.root), "--skill-dir", str(ONTOLOGY_SKILL)])
            self.onto.main(["init", "--write", "--root", str(self.root), "--skill-dir", str(ONTOLOGY_SKILL), "--by", "Tester", "--decisions", str(decisions)])
        with Quiet():
            engine.main(["init", "--root", str(self.root), "--slug", "o", "--mode", "local", "--skill-dir", str(SKILL_DIR), "--no-raw"])

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def q(self, sql, *params):
        conn = sqlite3.connect(f"file:{self.root / '.claude/db/project.sqlite'}?mode=ro", uri=True)
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def test_clean_vault_then_planted_error(self):
        self.assertEqual(self.q("SELECT * FROM ontology_violations"), [])
        self.assertGreater(self.q("SELECT COUNT(*) FROM ontology_terms WHERE status='approved'")[0][0], 5)
        self.assertEqual(self.q("SELECT ontology_id FROM pages WHERE slug='gap-a'")[0][0], "client.acme.gap.gap-a")
        self.assertEqual(self.q("SELECT ontology_id FROM gaps WHERE slug='gap-b'")[0][0], "client.acme.gap.gap-b")
        gap = self.root / "wiki/clients/acme/gaps/gap-a.md"
        gap.write_text(gap.read_text().replace("severity: high", "severity: urgent"))
        cfg = engine.load_config(self.root)
        engine.do_sync(self.root, cfg, full=False)
        rows = self.q("SELECT path, rule, policy, field, value, suggestion FROM ontology_violations")
        self.assertEqual(len(rows), 1)
        path, rule, policy, field, value, suggestion = rows[0]
        self.assertEqual((path, rule, policy, field, value), ("clients/acme/gaps/gap-a.md", "value-unknown", "strict", "severity", "urgent"))
        self.assertIn("critical", suggestion)

    def test_schema_docs_banner_verify_and_search(self):
        doc = self.q("SELECT doc FROM column_docs WHERE object='gaps' AND column='severity'")[0][0]
        self.assertEqual(doc, "→ gap.severity: critical|high|low")
        schema = (self.root / ".claude/db/SCHEMA.md").read_text()
        self.assertIn("## Ontology — controlled vocabulary", schema)
        cfg = engine.load_config(self.root)
        self.assertIn("ontology: ", engine.banner(self.root, cfg))
        conn = engine.open_ro(self.root, cfg, 5)
        try:
            _, rows = engine.fts_search(conn, "Acme Corp", None, 10, False)
        finally:
            conn.close()
        self.assertIn("gap-b", [r[0] for r in rows], "an alias finds pages that use the canonical value")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as cm:
                engine.main(["verify", "--root", str(self.root)])
        self.assertEqual(cm.exception.code, 0, out.getvalue())
        self.assertIn("ontology loaded into the database", out.getvalue())

    def test_gate_fail_exits_nonzero_on_strict_violations(self):
        cfg = engine.load_config(self.root)
        cfg["ontology"] = {"gate": "fail"}
        engine.save_config(self.root, cfg)
        gap = self.root / "wiki/clients/acme/gaps/gap-b.md"
        gap.write_text(gap.read_text().replace("See [[gap-a]]", "See [[nowhere]]"))
        err = io.StringIO()
        with Quiet(), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                engine.main(["sync", "--root", str(self.root)])
        self.assertEqual(cm.exception.code, 3)
        self.assertIn("strict ontology violation", err.getvalue())

    def test_broken_vendored_engine_never_breaks_sync(self):
        (self.root / ".claude/ontology/ontology.py").write_text("raise RuntimeError('boom')\n")
        cfg = engine.load_config(self.root)
        stats = engine.do_sync(self.root, cfg, full=False)
        self.assertIn("boom", stats["ontology"]["error"])
        self.assertEqual(self.q("SELECT COUNT(*) FROM pages")[0][0], 5)  # _index, _log, README, gap-a, gap-b

    def test_old_schema_version_rebuilds_with_ontology_tables(self):
        conn = sqlite3.connect(self.root / ".claude/db/project.sqlite")
        conn.execute("UPDATE sync_state SET value='1' WHERE key='schema_version'")
        conn.execute("DROP TABLE ontology_terms")
        conn.commit()
        conn.close()
        stats = engine.do_sync(self.root, engine.load_config(self.root), full=False)
        self.assertTrue(stats["full"])
        self.assertGreater(self.q("SELECT COUNT(*) FROM ontology_terms")[0][0], 0)


class HookPathTests(unittest.TestCase):
    def test_sessionstart_hook_is_quoted_and_old_entries_upgrade(self):
        root = Path(tempfile.mkdtemp(prefix="project-db space test-")) / "my project"
        try:
            write(root / "wiki" / "_index.md", "---\ntype: index\nupdated: 2020-01-01\n---\n# Index\n")
            write(root / "wiki" / "_log.md", "---\ntype: log\nupdated: 2020-01-01\n---\n# Log\n")
            write(root / ".claude/settings.json", json.dumps({"hooks": {"SessionStart": [{"hooks": [
                {"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/db-context.sh", "timeout": 30}]}]}}))
            with Quiet():
                engine.main(["init", "--root", str(root), "--slug", "s", "--mode", "local", "--skill-dir", str(SKILL_DIR), "--no-raw"])
            cmds = [h["command"] for e in json.loads((root / ".claude/settings.json").read_text())["hooks"]["SessionStart"] for h in e["hooks"]]
            self.assertEqual(cmds, ['"$CLAUDE_PROJECT_DIR"/.claude/hooks/db-context.sh'])
            import subprocess
            p = subprocess.run(["bash", "-c", cmds[0]], input="{}", capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("project-db", p.stdout)
            self.assertIn(f"updated: {engine.now_iso()[:10]}", (root / "wiki/_log.md").read_text().split("---", 2)[1])
        finally:
            shutil.rmtree(root.parent, ignore_errors=True)


class NoWikiTests(unittest.TestCase):
    def test_markdown_collection_gets_default_type_and_standalone_mandate(self):
        root = Path(tempfile.mkdtemp(prefix="project-db-nowiki-"))
        try:
            write(root / "docs/adr/0001-x.md", "---\nstatus: accepted\n---\n# ADR 1\n")
            write(root / "docs/adr/0002-y.md", "# ADR 2 without frontmatter\n")
            with Quiet():
                engine.main(["init", "--root", str(root), "--slug", "nw", "--mode", "local", "--skill-dir", str(SKILL_DIR), "--no-wiki", "--markdown", "adr=docs/adr"])
            conn = sqlite3.connect(f"file:{root / '.claude/db/project.sqlite'}?mode=ro", uri=True)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM adrs").fetchone()[0], 2)
            self.assertEqual(conn.execute("SELECT status FROM adrs WHERE slug='0001-x'").fetchone()[0], "accepted")
            conn.close()
            self.assertIn("source of truth", (root / "CLAUDE.md").read_text())
            self.assertTrue((root / ".claude/db/LOG.md").exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
