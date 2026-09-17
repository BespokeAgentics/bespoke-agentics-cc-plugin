#!/usr/bin/env python3
"""Regression tests for the project-ontology engine. Stdlib only.

Run from anywhere:  python3 <skill>/scripts/test_ontology.py
Each test builds a throwaway vault in a temp dir, so nothing here touches a real wiki. Every test names
the behaviour it pins; the acceptance criteria of docs/plans/project-ontology.md each have one.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ontology as engine  # noqa: E402

SKILL_DIR = HERE.parent
PLUGIN_ROOT = SKILL_DIR.parent.parent
DB_ENGINE = PLUGIN_ROOT / "skills" / "project-db" / "scripts" / "db.py"


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


SCHEMA = """# Schema

### Gap

**Definition**: A difference between the legacy platform and the target.

```yaml
---
type: gap
client: acme
severity: critical|high|medium|low  # impact
status: open|under-review|resolved
---
```

```yaml
---
type: gap|feature
client: {client-slug}|shared
---
```

```yaml
---
type: feature
status: active|deprecated
---
```

Example link that must not count: [[Budget Management]]
"""

GAP_ONE = """---
type: gap
client: acme
status: open
severity: critical
related-feature: "[[feat-one]]"
tags: [alpha, beta]
---

# Gap One

Links: [[feat-one]] and [[Feature One]] and [[gap|gap-two]] and [[shared-name]].

```
[[inside-code-fence]]
```
<!-- [[inside-comment]] -->
Inline `[[inside-inline-code]]` too.
"""

GAP_TWO = """---
type: gap
client: Acme
status: mitigated
severity: high
tags: alpha, gamma
---

# Gap Two
"""

FEAT_ONE = """---
type: feature
client: acme
status: draft
priority: P0
category: catalog
tags:
  - alpha
---

# Feature One
"""


class Vault:
    """A tiny vault; init with defaults on demand; torn down after each test."""

    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="project-ontology-test-"))
        w = self.root / "wiki"
        write(w / "_index.md", "---\ntype: index\n---\n# Index\n\n[[SCHEMA]] · [[gap-one]]\n")
        write(w / "_log.md", "---\ntype: log\n---\n# Log\n\n## 2026-01-01 — created\n\nfirst entry\n")
        write(w / "_schema" / "SCHEMA.md", SCHEMA)
        write(w / "_schema" / "templates" / "gap.md", "---\ntype: gap\nclient:\nstatus: # open|mitigated|resolved\nseverity: # critical|high|medium|low\nrelated-feature:\ntags:\n---\n# Gap\n")
        write(w / "_schema" / "templates" / "feature.md", "---\ntype: feature\nclient:\nstatus:\npriority: # P1|P2|P3\ncategory: # catalog|ordering\ntags:\n---\n# Feature\n")
        write(w / "clients" / "acme" / "README.md", "# Acme — client overview\n")
        write(w / "clients" / "acme" / "gaps" / "gap-one.md", GAP_ONE)
        write(w / "clients" / "acme" / "gaps" / "gap-two.md", GAP_TWO)
        write(w / "clients" / "acme" / "gaps" / "shared-name.md", "---\ntype: gap\nclient: acme\nstatus: open\nseverity: low\n---\n# Shared gap\n")
        write(w / "clients" / "acme" / "features" / "feat-one.md", FEAT_ONE)
        write(w / "clients" / "acme" / "features" / "shared-name.md", "---\ntype: feature\nclient: acme\npriority: P1\n---\n# Shared feature\n")
        write(w / "platforms" / "acme-cloud" / "overview.md", "---\ntype: platform\n---\n# Acme Cloud — overview\n")
        write(w / "notes" / "untyped.md", "# Untyped\n\nSee [[missing-page]] and ![[diagram.png]].\n")
        write(w / "notes" / "diagram.png", "png")
        write(self.root / "CLAUDE.md", "# Existing\n\nkeep me\n")

    def run(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                engine.main(list(argv))
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        return code, out.getvalue(), err.getvalue()

    def init(self, decisions: dict | None = None, *extra: str) -> dict:
        self.run("init", "--scan", "--root", str(self.root), "--skill-dir", str(SKILL_DIR))
        args = ["init", "--write", "--root", str(self.root), "--skill-dir", str(SKILL_DIR), "--by", "Test Human", *extra]
        if decisions is not None:
            dp = self.root / "decisions.json"
            dp.write_text(json.dumps(decisions), encoding="utf-8")
            args += ["--decisions", str(dp)]
        code, out, err = self.run(*args)
        self.last_init = (code, out, err)
        return json.loads(out) if out.strip().startswith("{") else {}

    def project(self) -> engine.Project:
        return engine.Project.load(self.root)

    def ontology_text(self) -> str:
        return (self.root / "wiki" / "_schema" / "ontology.yaml").read_text(encoding="utf-8")

    def check(self, rel: str, text: str | None = None) -> list[dict]:
        proj = self.project()
        index = engine.FileIndex(proj, overrides={rel: text} if text is not None else None)
        return engine.check_text(proj, rel, text if text is not None else index.text(rel), index)

    def pre(self, tool: str, rel: str, **tool_input) -> tuple[int, str]:
        data = {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(self.root),
                "tool_input": dict(file_path=str(self.root / rel), **tool_input)}
        return engine.hook_pre(data, self.root)

    def close(self):
        shutil.rmtree(self.root, ignore_errors=True)


def rules(viols, policy=None):
    return sorted({(v["rule"], str(v.get("value"))) for v in viols if policy is None or v["policy"] == policy})


class TestParsing(unittest.TestCase):
    def test_frontmatter_parity_with_project_db(self):
        """The hook and the database must read identical values — same parser semantics as project-db."""
        if not DB_ENGINE.exists():
            self.skipTest("project-db engine not present next to this skill")
        import importlib.util
        spec = importlib.util.spec_from_file_location("projectdb_engine", DB_ENGINE)
        db = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db)
        samples = [GAP_ONE, GAP_TWO, FEAT_ONE,
                   "---\nkey: 'quoted # not comment'\nlist: [a, \"b, c\", [[x]]]\nlinks: [[A]], [[B]]\nn: 12\nf: 1.5\nb: yes\nempty:\nmap:\n  k: v\n---\n",
                   "---\ntags:\n- one\n- two\nnext: value\n---\n"]
        for s in samples:
            fm, _ = engine.split_frontmatter(s)
            ours, _ = engine.parse_frontmatter(fm)
            theirs, _ = db.parse_yaml_subset(fm)
            self.assertEqual(ours, theirs, s[:60])

    def test_unindented_block_list_is_a_list(self):
        data, _ = engine.parse_frontmatter("tags:\n- one\n- two\nstatus: open")
        self.assertEqual(data, {"tags": ["one", "two"], "status": "open"})

    def test_frontmatter_items_spans_and_lines(self):
        text = FEAT_ONE
        data, items, body_at = engine.frontmatter_items(text)
        for it in items:
            self.assertEqual(text[it["start"]:it["end"]], it["raw"])
        by = {(i["key"], i["index"]): i for i in items}
        self.assertEqual(by[("priority", 0)]["line"], 5)
        self.assertEqual(by[("tags", 0)]["raw"], "alpha")
        self.assertTrue(text[body_at:].lstrip().startswith("# Feature One"))
        _, items2, _ = engine.frontmatter_items(GAP_ONE)
        tag_items = [i for i in items2 if i["key"] == "tags"]
        self.assertEqual([i["raw"] for i in tag_items], ["alpha", "beta"])
        self.assertEqual([GAP_ONE[i["start"]:i["end"]] for i in tag_items], ["alpha", "beta"])

    def test_visible_body_ignores_code_and_comments_and_keeps_lines(self):
        body = GAP_ONE.split("---\n", 2)[2]
        shown = engine.visible_body(body)
        self.assertEqual(body.count("\n"), shown.count("\n"))
        targets = [m.group(1) for m in engine.WIKILINK_RE.finditer(shown)]
        self.assertNotIn("inside-code-fence", targets)
        self.assertNotIn("inside-comment", targets)
        self.assertNotIn("inside-inline-code", targets)
        self.assertIn("feat-one", targets)

    def test_ontology_yaml_roundtrip_and_quoting(self):
        data = {"version": 1, "name": "t", "policy": {"default": "strict", "overrides": {"tag": "warn"}},
                "fields": {"*.type": {"kind": "type"}},
                "types": {"type.gap": {"label": "Gap", "status": "approved"}},
                "vocabularies": {"gap.severity.p1": {"label": "yes", "value": "P1", "definition": "it's: a [x] #tag, with commas", "status": "approved",
                                                     "aliases": ["a, b", "it's", "🟡", "true"]}},
                "entities": {}, "relations": {}, "tags": {}}
        text = engine.dump_onto_yaml(data)
        back = engine.parse_onto_yaml(text)
        self.assertEqual(back["vocabularies"]["gap.severity.p1"]["aliases"], ["a, b", "it's", "🟡", "true"])
        self.assertEqual(back["vocabularies"]["gap.severity.p1"]["definition"], "it's: a [x] #tag, with commas")
        self.assertEqual(back["vocabularies"]["gap.severity.p1"]["label"], "yes")
        self.assertEqual(engine.dump_onto_yaml(back), text)

    def test_ontology_yaml_errors_name_the_line(self):
        for bad, needle in (("a:\n\tb: 1\n", "line 2"), ("a: {b: 1}\n", "line 1"), ("a: 'open\n", "line 1"),
                            ("a: 1\na: 2\n", "duplicate"), ("types:\n  - x\n  k: v\n", "line 3")):
            with self.assertRaises(engine.OntologyError) as cm:
                engine.parse_onto_yaml(bad)
            self.assertIn(needle, str(cm.exception))


class TestModel(unittest.TestCase):
    def onto(self, **over):
        data = {"policy": {"default": "strict", "overrides": {"tag": "warn", "gap.status": "warn"}},
                "fields": {"*.type": {"kind": "type"}, "gap.severity": {"kind": "vocab"}, "gap.status": {"kind": "vocab"},
                           "*.client": {"kind": "entity", "namespace": "client"}, "*.tags": {"kind": "tag"}},
                "types": {"type.gap": {"status": "approved"}},
                "vocabularies": {"gap.severity.critical": {"status": "approved", "aliases": ["crit"], "proposed-aliases": ["blocker"]},
                                 "gap.severity.high": {"status": "approved"},
                                 "gap.severity.urgent": {"status": "deprecated", "replaced-by": "gap.severity.critical"},
                                 "gap.severity.p1": {"status": "proposed", "value": "P1"},
                                 "gap.status.open": {"status": "approved"}},
                "entities": {"client.acme-corp": {"status": "approved"}}, "relations": {}, "tags": {"tag.gap.critical": {"status": "approved"}}}
        data.update(over)
        return engine.Ontology(data)

    def test_match_kinds(self):
        o = self.onto()
        self.assertEqual(o.match("vocab", "gap.severity", "critical")[1], "canonical")
        self.assertEqual(o.match("vocab", "gap.severity", "crit")[1], "alias")
        self.assertEqual(o.match("vocab", "gap.severity", "blocker")[1], "proposed-alias")
        self.assertEqual(o.match("vocab", "gap.severity", "Critical")[1], "variant")
        self.assertEqual(o.match("vocab", "gap.severity", "p1")[0]["_id"], "gap.severity.p1")
        self.assertEqual(o.match("entity", "client", "Acme Corp")[1], "variant")
        self.assertEqual(o.match("tag", None, "gap/critical")[1], "canonical")
        self.assertEqual(o.match("vocab", "gap.severity", "nope"), (None, None))

    def test_policy_most_specific_wins_and_proposed_is_capped(self):
        o = self.onto()
        self.assertEqual(o.policy_for("value-unknown", "vocab", "gap.status", "gap"), "warn")
        self.assertEqual(o.policy_for("value-unknown", "vocab", "gap.severity", "gap"), "strict")
        self.assertEqual(o.policy_for("value-unknown", "tag", "*.tags", "tag"), "warn")
        self.assertEqual(o.policy_for("value-proposed", "vocab", "gap.severity", "gap"), "warn")
        o2 = self.onto(policy={"default": "strict", "proposed": "strict"})
        self.assertEqual(o2.policy_for("value-proposed", "vocab", "gap.severity", "gap"), "strict")

    def test_malformed_sections_are_errors_not_crashes(self):
        o = engine.Ontology({"types": ["type.gap"], "fields": "nope", "policy": "strict", "vocabularies": {"gap.x.y": "approved"}})
        joined = "\n".join(o.errors)
        self.assertIn("types: expected a mapping", joined)
        self.assertIn("fields: expected a mapping", joined)
        self.assertIn("policy: expected a mapping", joined)
        self.assertIn("gap.x.y: a term is a mapping", joined)

    def test_wildcard_vocabulary_skips_untyped_pages(self):
        v = Vault()
        try:
            v.init()
            proj = v.project()
            proj.onto.fields["*.status"] = {"kind": "vocab"}
            index = engine.FileIndex(proj)
            text = "---\nstatus: whatever\n---\n# Untyped\n"
            self.assertEqual([x for x in engine.check_text(proj, "wiki/notes/untyped.md", text, index) if x.get("field") == "status"], [])
        finally:
            v.close()

    def test_validation_errors(self):
        o = engine.Ontology({"fields": {"gap.x": {"kind": "relation", "relation": "rel.none"}, "bad": {"kind": "vocab"}},
                             "types": {"type.gap": {"status": "approved"}, "type.Bad": {"status": "approved"}},
                             "vocabularies": {"feature.status.open": {"status": "approved"}, "gap.status.open": {"status": "maybe"},
                                              "gap.status.closed": {"status": "deprecated", "replaced-by": "gap.status.gone"},
                                              "gap.status.shut": {"status": "approved", "value": "open"}},
                             "entities": {}, "relations": {}, "tags": {}})
        joined = "\n".join(o.errors)
        for needle in ("type.Bad", "feature.status.open", "status must be one of", "gap.status.gone", "rel.none", "fields.bad", "already belongs"):
            self.assertIn(needle, joined)


class TestRules(unittest.TestCase):
    def setUp(self):
        self.v = Vault()
        self.v.init()

    def tearDown(self):
        self.v.close()

    def test_value_rules_unknown_noncanonical_proposed(self):
        viols = self.v.check("wiki/clients/acme/features/feat-one.md")
        got = rules(viols)
        self.assertIn(("value-proposed", "draft"), got)      # observed-only value → proposed (warn)
        self.assertIn(("value-proposed", "P0"), got)
        self.assertTrue(all(v["policy"] == "warn" for v in viols if v["rule"] == "value-proposed"))
        viols2 = self.v.check("wiki/clients/acme/gaps/gap-two.md")
        self.assertIn(("value-noncanonical", "Acme"), rules(viols2))  # variant of client.acme
        text = GAP_TWO.replace("severity: high", "severity: urgent").replace("client: Acme", "client: acme")
        v3 = [v for v in self.v.check("wiki/clients/acme/gaps/gap-two.md", text) if v["rule"] == "value-unknown"]
        self.assertEqual(len(v3), 1)
        self.assertEqual(v3[0]["policy"], "strict")
        self.assertIn("approved: critical · high · medium · low", v3[0]["suggestion"])
        self.assertIn("propose gap.severity.urgent", v3[0]["fix"])
        near = [v for v in self.v.check("wiki/clients/acme/gaps/gap-two.md", text.replace("urgent", "critcal")) if v["rule"] == "value-unknown"]
        self.assertEqual(near[0]["nearest"][0], "critical")

    def test_tags_warn_by_default_and_comma_strings_split(self):
        viols = self.v.check("wiki/clients/acme/gaps/gap-two.md")
        tag_vals = sorted(v["value"] for v in viols if v["family"] == "tag")
        self.assertEqual(tag_vals, ["alpha", "gamma"])
        text = GAP_TWO.replace("tags: alpha, gamma", "tags: alpha, brand-new-tag")
        new = [v for v in self.v.check("wiki/clients/acme/gaps/gap-two.md", text) if v["rule"] == "value-unknown"]
        self.assertEqual([(v["value"], v["policy"]) for v in new], [("brand-new-tag", "warn")])

    def test_type_rules_and_ignored_types(self):
        text = "---\ntype: gizmo\nclient: acme\n---\n# X\n"
        got = rules(self.v.check("wiki/clients/acme/gaps/x.md", text))
        self.assertIn(("type-unknown", "gizmo"), got)
        idx = self.v.check("wiki/_index.md")
        self.assertFalse([v for v in idx if v["family"] in ("vocab", "entity", "tag")])

    def test_link_rules(self):
        viols = self.v.check("wiki/clients/acme/gaps/gap-one.md")
        by_value = {v["value"]: v for v in viols if v["family"] == "link"}
        self.assertNotIn("[[feat-one]]", by_value)                           # exact → ok
        self.assertEqual(by_value["[[Feature One]]"]["rule"], "link-noncanonical")  # title
        self.assertEqual(by_value["[[Feature One]]"]["replacement"], "[[feat-one|Feature One]]")
        self.assertEqual(by_value["[[gap|gap-two]]"]["rule"], "link-noncanonical")  # label form
        self.assertEqual(by_value["[[gap|gap-two]]"]["replacement"], "[[gap-two]]")
        amb = by_value["[[shared-name]]"]
        self.assertEqual(amb["rule"], "link-ambiguous")
        self.assertIn("[[clients/acme/gaps/shared-name]]", amb["suggestion"])  # full vault path, not a suffix
        for hidden in ("[[inside-code-fence]]", "[[inside-comment]]", "[[inside-inline-code]]"):
            self.assertNotIn(hidden, by_value)
        untyped = {v["value"]: v["rule"] for v in self.v.check("wiki/notes/untyped.md")}
        self.assertEqual(untyped.get("[[missing-page]]"), "link-broken")
        self.assertNotIn("![[diagram.png]]", untyped)
        self.assertNotIn("[[diagram.png]]", untyped)

    def test_label_links_use_the_type_word_to_disambiguate(self):
        text = GAP_ONE.replace("[[gap|gap-two]]", "[[feature|shared-name]]")
        v = [x for x in self.v.check("wiki/clients/acme/gaps/gap-one.md", text) if x["value"] == "[[feature|shared-name]]"][0]
        self.assertEqual(v["rule"], "link-noncanonical")
        self.assertEqual(v["resolved"], "wiki/clients/acme/features/shared-name.md")
        self.assertEqual(v["replacement"], "[[clients/acme/features/shared-name|shared-name]]")

    def test_templates_are_not_link_targets(self):
        text = GAP_ONE.replace("[[gap|gap-two]]", "[[gap|does-not-exist]]")
        v = [x for x in self.v.check("wiki/clients/acme/gaps/gap-one.md", text) if x["value"] == "[[gap|does-not-exist]]"][0]
        self.assertEqual(v["rule"], "link-broken")  # would "resolve" to _schema/templates/gap.md otherwise

    def test_relation_rules(self):
        base = "wiki/clients/acme/gaps/gap-one.md"
        self.assertFalse([v for v in self.v.check(base) if v["family"] == "relation"])
        bad_range = GAP_ONE.replace('related-feature: "[[feat-one]]"', 'related-feature: "[[gap-two]]"')
        self.assertIn(("relation-range", "[[gap-two]]"), rules(self.v.check(base, bad_range)))
        not_link = GAP_ONE.replace('related-feature: "[[feat-one]]"', "related-feature: feat-one")
        self.assertIn(("relation-broken", "feat-one"), rules(self.v.check(base, not_link)))

    def test_derived_ids(self):
        proj = self.v.project()
        self.assertEqual(proj.derive_id("wiki/clients/acme/gaps/gap-one.md", "gap"), "client.acme.gap.gap-one")
        self.assertEqual(proj.derive_id("wiki/clients/acme/README.md", None), "client.acme")
        self.assertEqual(proj.derive_id("wiki/platforms/acme-cloud/overview.md", "platform"), "platform.acme-cloud")
        self.assertEqual(proj.derive_id("wiki/notes/untyped.md", None), "page.untyped")

    def test_id_duplicate(self):
        write(self.v.root / "wiki" / "clients" / "acme" / "gaps" / "Gap_One.md", "---\ntype: gap\nclient: acme\n---\n# dup\n")
        viols, pages = engine.check_all(self.v.project())
        dups = [v for v in viols if v["rule"] == "id-duplicate"]
        self.assertEqual(len(dups), 2)


class TestRobustness(unittest.TestCase):
    def test_odd_inputs_never_raise(self):
        """The pre hook fails closed on an engine crash, so the rules must not crash on odd pages."""
        v = Vault()
        try:
            v.init()
            odd = ["", "---", "---\n", "---\ntype: gap\n", "---\n---\n", "---\ntype: gap\n---", "\ufeff---\ntype: gap\n---\n",
                   "---\ntype: [gap, feature]\nseverity: {x: 1}\ntags: [[[\n---\n", "---\ntype: gap\ntags: 'unterminated\n---\n",
                   "---\r\ntype: gap\r\nseverity: urgent\r\n---\r\n# crlf [[nowhere]]\r\n", "[[" * 500, "---\ntype: |\n  gap\n---\n",
                   "---\n\ttype: gap\n---\n", "# no frontmatter [[a|b|c]] [[#heading]] [[]] [[ ]]\n", "x" * 200000]
            for i, text in enumerate(odd):
                v.check(f"wiki/clients/acme/gaps/odd-{i}.md", text)
            crlf = [x for x in v.check("wiki/clients/acme/gaps/crlf.md", odd[9]) if x["rule"] == "value-unknown"]
            self.assertEqual([x["value"] for x in crlf], ["urgent"])
        finally:
            v.close()


class TestHooks(unittest.TestCase):
    def setUp(self):
        self.v = Vault()
        self.v.init()

    def tearDown(self):
        self.v.close()

    NEW_GAP = "---\ntype: gap\nclient: acme\nstatus: open\nseverity: {sev}\n---\n# New gap\n"

    def test_write_with_unknown_severity_is_blocked_naming_approved_terms(self):
        """Acceptance: writing a gap page with `severity: urgent` is blocked (strict) with the nearest approved terms named."""
        code, msg = self.v.pre("Write", "wiki/clients/acme/gaps/new.md", content=self.NEW_GAP.format(sev="urgent"))
        self.assertEqual(code, 2)
        self.assertIn("severity: `urgent` is not a registered gap.severity value", msg)
        self.assertIn("approved: critical · high · medium · low", msg)
        self.assertIn("propose gap.severity.urgent", msg)
        ok, _ = self.v.pre("Write", "wiki/clients/acme/gaps/new.md", content=self.NEW_GAP.format(sev="high"))
        self.assertEqual(ok, 0)

    def test_ratchet_existing_violations_do_not_block_new_ones_do(self):
        rel = "wiki/clients/acme/gaps/gap-one.md"
        code, _ = self.v.pre("Edit", rel, old_string="# Gap One", new_string="# Gap One (edited)")
        self.assertEqual(code, 0)  # the page already has noncanonical/ambiguous links: not this edit's doing
        code, msg = self.v.pre("Edit", rel, old_string="severity: critical", new_string="severity: urgent")
        self.assertEqual(code, 2)
        self.assertIn("1 new strict violation", msg)
        code, msg = self.v.pre("Edit", rel, old_string="# Gap One", new_string="# Gap One\n\nAlso [[feat-one]] again.")
        self.assertEqual(code, 0)  # a valid link adds nothing
        code, msg = self.v.pre("Edit", rel, old_string="# Gap One", new_string="# Gap One\n\nAlso [[nowhere-page]].")
        self.assertEqual(code, 2)
        self.assertIn("link-broken", msg)

    def test_duplicate_of_existing_violation_counts_as_new(self):
        rel = "wiki/clients/acme/gaps/gap-two.md"
        text = (self.v.root / rel).read_text()
        doubled = text.replace("# Gap Two", "# Gap Two\n\n[[Missing A]]\n")
        write(self.v.root / rel, doubled)
        code, msg = self.v.pre("Edit", rel, old_string="[[Missing A]]\n", new_string="[[Missing A]]\n[[Missing A]]\n")
        self.assertEqual(code, 2)

    def test_edit_simulation_semantics(self):
        rel = "wiki/clients/acme/gaps/gap-one.md"
        self.assertEqual(engine.simulate_write("Edit", {"old_string": "not there", "new_string": "x"}, "abc"), None)
        self.assertEqual(engine.simulate_write("Edit", {"old_string": "a", "new_string": "x"}, "a a"), None)
        self.assertEqual(engine.simulate_write("Edit", {"old_string": "a", "new_string": "x", "replace_all": True}, "a a"), "x x")
        self.assertEqual(engine.simulate_write("MultiEdit", {"edits": [{"old_string": "a", "new_string": "b"}, {"old_string": "b c", "new_string": "d"}]}, "a c"), "d")
        self.assertEqual(engine.simulate_write("Edit", {"old_string": "", "new_string": "new file"}, None), "new file")
        code, _ = self.v.pre("Edit", rel, old_string="severity", new_string="x")  # not unique → tool will fail → stay out
        self.assertEqual(code, 0)
        code, _ = self.v.pre("MultiEdit", rel, edits=[{"old_string": "# Gap One", "new_string": "# G"}, {"old_string": "severity: critical", "new_string": "severity: urgent"}])
        self.assertEqual(code, 2)

    def test_field_name_variants_from_docs(self):
        data = {"tool_name": "Write", "cwd": str(self.v.root),
                "tool_input": {"path": str(self.v.root / "wiki/clients/acme/gaps/new.md"), "contents": self.NEW_GAP.format(sev="urgent")}}
        self.assertEqual(engine.hook_pre(data, self.v.root)[0], 2)

    def test_non_governed_files_pass(self):
        for rel in ("wiki/_schema/templates/gap.md", "wiki/clients/acme/notes.txt", "src/app.md", "CLAUDE.md"):
            self.assertEqual(self.v.pre("Write", rel, content="---\ntype: gap\nseverity: urgent\n---\n")[0], 0, rel)

    def test_ontology_file_guard(self):
        rel = "wiki/_schema/ontology.yaml"
        text = self.v.ontology_text()
        approve = text.replace("    label: draft\n    status: proposed", "    label: draft\n    status: approved", 1)
        self.assertNotEqual(approve, text)
        code, msg = self.v.pre("Write", rel, content=approve)
        self.assertEqual(code, 2)
        self.assertIn("human gate", msg)
        proposal = text.replace("vocabularies:\n", "vocabularies:\n  gap.severity.urgent:\n    label: Urgent\n    definition: now\n    status: proposed\n", 1)
        self.assertEqual(self.v.pre("Write", rel, content=proposal)[0], 0)
        self.assertEqual(self.v.pre("Write", rel, content=text + "\nbroken: {x: 1}\n")[0], 2)
        sneaky = approve.replace("approval: human", "approval: agent")
        code, msg = self.v.pre("Write", rel, content=sneaky)
        self.assertEqual(code, 2)  # flipping approval to agent in the same write is itself gated
        self.assertIn("policy.approval: human → agent", msg)
        removal = text.replace("  gap.severity.low:\n", "  gap.severity.gone:\n", 1)
        self.assertEqual(self.v.pre("Write", rel, content=removal)[0], 2)  # approved term removed/renamed
        loosen = text.replace("default: strict", "default: warn", 1)
        self.assertEqual(self.v.pre("Write", rel, content=loosen)[0], 2)
        agent_ok = approve.replace("approval: human", "approval: agent")
        write(self.v.root / rel, text.replace("approval: human", "approval: agent"))
        self.assertEqual(self.v.pre("Write", rel, content=agent_ok)[0], 0)

    def test_broken_ontology_fails_closed_for_pages(self):
        write(self.v.root / "wiki/_schema/ontology.yaml", "types: {broken\n")
        code, msg = self.v.pre("Write", "wiki/clients/acme/gaps/new.md", content=self.NEW_GAP.format(sev="high"))
        self.assertEqual(code, 2)
        self.assertIn("cannot be loaded", msg)

    def test_post_hook_reports_non_blocking_context(self):
        rel = "wiki/clients/acme/features/feat-one.md"
        data = {"tool_name": "Edit", "cwd": str(self.v.root), "tool_input": {"file_path": str(self.v.root / rel)}}
        code, out = engine.hook_post(data, self.v.root)
        self.assertEqual(code, 0)
        ctx = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(ctx["hookEventName"], "PostToolUse")
        self.assertIn("draft", ctx["additionalContext"])

    def test_bash_hook(self):
        def bash(cmd):
            return engine.hook_bash({"tool_name": "Bash", "cwd": str(self.v.root), "tool_input": {"command": cmd}}, self.v.root)
        code, out = bash("python3 .claude/ontology/ontology.py approve gap.severity.urgent --by Me")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "ask")
        self.assertEqual(bash("sed -i '' 's/high/urgent/' wiki/clients/acme/gaps/gap-two.md")[0], 2)
        self.assertEqual(bash("echo 'severity: urgent' >> wiki/clients/acme/gaps/gap-two.md")[0], 2)
        self.assertEqual(bash("printf x | tee wiki/clients/acme/gaps/new.md")[0], 2)
        self.assertEqual(bash("cp /tmp/x.md wiki/clients/acme/gaps/copy.md")[0], 2)
        self.assertEqual(bash("cat wiki/clients/acme/gaps/gap-two.md | grep severity")[0], 0)
        self.assertEqual(bash("sed -n 1,5p wiki/clients/acme/gaps/gap-two.md")[0], 0)
        self.assertEqual(bash("echo hi > notes.md")[0], 0)
        self.assertEqual(bash("python3 .claude/ontology/ontology.py propose gap.severity.urgent --definition x")[0], 0)
        code, out = bash("python3 .claude/ontology/ontology.py init --write --decisions d.json --by Me")
        self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "ask")
        self.assertEqual(bash("python3 .claude/ontology/ontology.py init --scan")[0], 0)

    def test_guard_script_end_to_end(self):
        if not shutil.which("bash"):
            self.skipTest("bash not available")
        payload = json.dumps({"tool_name": "Write", "cwd": str(self.v.root),
                              "tool_input": {"file_path": str(self.v.root / "wiki/clients/acme/gaps/new.md"), "content": self.NEW_GAP.format(sev="urgent")}})
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.v.root))
        p = subprocess.run([str(self.v.root / engine.GUARD_HOOK_REL), "pre"], input=payload, capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 2)
        self.assertIn("urgent", p.stderr)
        t0 = time.time()
        p = subprocess.run([str(self.v.root / engine.GUARD_HOOK_REL), "bash"], input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}),
                           capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0)
        self.assertLess(time.time() - t0, 1.0)  # fast path never starts python for unrelated commands


class TestGovernance(unittest.TestCase):
    def setUp(self):
        self.v = Vault()
        self.v.init()

    def tearDown(self):
        self.v.close()

    def test_proposal_then_approval_clears_the_violation(self):
        """Acceptance (eval discipline): a planted bad value is listed; propose → warn; approve → clean."""
        rel = "wiki/clients/acme/gaps/gap-two.md"
        write(self.v.root / rel, (self.v.root / rel).read_text().replace("severity: high", "severity: urgent"))
        sev = lambda: [(v["rule"], v["policy"]) for v in self.v.check(rel) if v.get("field") == "severity"]
        self.assertEqual(sev(), [("value-unknown", "strict")])
        code, out, err = self.v.run("propose", "gap.severity.urgent", "--label", "Urgent", "--root", str(self.v.root))
        self.assertNotEqual(code, 0)
        self.assertIn("--definition is required", err)
        code, out, err = self.v.run("propose", "gap.severity.urgent", "--label", "Urgent", "--definition", "Must ship this week", "--root", str(self.v.root))
        self.assertEqual(code, 0, err)
        self.assertEqual(sev(), [("value-proposed", "warn")])
        code, out, err = self.v.run("approve", "gap.severity.urgent", "--root", str(self.v.root))
        self.assertNotEqual(code, 0)
        code, out, err = self.v.run("approve", "gap.severity.urgent", "--by", "Test Human", "--root", str(self.v.root))
        self.assertEqual(code, 0, err)
        self.assertEqual(sev(), [])
        log = (self.v.root / "wiki/_log.md").read_text()
        self.assertIn("ontology proposal — gap.severity.urgent", log)
        self.assertIn("Approved by Test Human", log)
        doc = (self.v.root / "wiki/_schema/ONTOLOGY.md").read_text()
        self.assertIn("`gap.severity.urgent`", doc)

    def test_propose_can_place_a_term_in_ranking_order(self):
        r = str(self.v.root)
        code, _, err = self.v.run("propose", "gap.severity.urgent", "--definition", "above critical", "--before", "gap.severity.critical", "--root", r)
        self.assertEqual(code, 0, err)
        order = [t for t in self.v.project().onto.terms if t.startswith("gap.severity.")]
        self.assertEqual(order[:2], ["gap.severity.urgent", "gap.severity.critical"])
        code, _, err = self.v.run("propose", "gap.severity.trivial", "--definition", "below low", "--after", "gap.severity.low", "--root", r)
        self.assertEqual(code, 0, err)
        self.assertEqual([t for t in self.v.project().onto.terms if t.startswith("gap.severity.")][-1], "gap.severity.trivial")
        code, _, err = self.v.run("propose", "gap.severity.odd", "--definition", "x", "--before", "gap.status.open", "--root", r)
        self.assertNotEqual(code, 0)
        self.assertIn("not a sibling", err)
        doc = (self.v.root / "wiki/_schema/ONTOLOGY.md").read_text()
        table = doc[doc.index("### `gap.severity`"):]
        self.assertLess(table.index("`gap.severity.urgent`"), table.index("`gap.severity.critical`"))

    def test_propose_on_uncontrolled_field_needs_bind(self):
        code, _, err = self.v.run("propose", "gap.effort.xl", "--definition", "big", "--root", str(self.v.root))
        self.assertNotEqual(code, 0)
        self.assertIn("--bind", err)
        code, _, err = self.v.run("propose", "gap.effort.xl", "--definition", "big", "--bind", "--root", str(self.v.root))
        self.assertEqual(code, 0, err)
        self.assertIn("gap.effort", self.v.project().onto.fields)

    def test_propose_alias_then_approve_moves_it(self):
        self.v.run("propose", "client.acme", "--alias", "ACME Inc", "--root", str(self.v.root))
        t = self.v.project().onto.terms["client.acme"]
        self.assertIn("ACME Inc", t["proposed-aliases"])
        self.v.run("approve", "client.acme", "--by", "Test Human", "--aliases-only", "--root", str(self.v.root))
        t = self.v.project().onto.terms["client.acme"]
        self.assertIn("ACME Inc", t["aliases"])
        self.assertIn("Acme", t["aliases"])  # the observed variant proposed at init rides along

    def test_deprecate_requires_compatible_replacement(self):
        r = str(self.v.root)
        code, _, err = self.v.run("deprecate", "gap.severity.low", "--replaced-by", "client.acme", "--by", "H", "--root", r)
        self.assertNotEqual(code, 0)
        code, _, err = self.v.run("deprecate", "gap.severity.low", "--replaced-by", "gap.severity.medium", "--reason", "merged", "--by", "H", "--root", r)
        self.assertEqual(code, 0, err)
        rel = "wiki/clients/acme/gaps/shared-name.md"
        v = [x for x in self.v.check(rel) if x.get("field") == "severity"][0]
        self.assertEqual((v["rule"], v["replacement"]), ("value-deprecated", "medium"))

    def test_apply_rewrites_mechanical_cases_and_preserves_other_bytes(self):
        r = str(self.v.root)
        self.v.run("deprecate", "gap.severity.low", "--replaced-by", "gap.severity.medium", "--by", "H", "--root", r)
        gap_two = self.v.root / "wiki/clients/acme/gaps/gap-two.md"
        gap_one = self.v.root / "wiki/clients/acme/gaps/gap-one.md"
        shared = self.v.root / "wiki/clients/acme/gaps/shared-name.md"
        before = {p: p.read_text() for p in (gap_two, gap_one, shared)}
        code, out, err = self.v.run("apply", "--dry-run", "--root", r)
        self.assertIn("would rewrite", out)
        self.assertEqual({p: p.read_text() for p in before}, before)
        code, out, err = self.v.run("apply", "--root", r)
        self.assertEqual(code, 0, err)
        self.assertIn("client: acme\n", gap_two.read_text())
        self.assertIn("severity: medium\n", shared.read_text())
        g1 = gap_one.read_text()
        self.assertIn("[[feat-one|Feature One]]", g1)
        self.assertIn("[[gap-two]]", g1)
        self.assertIn("[[shared-name]]", g1)  # ambiguous: a judgment call, left alone
        self.assertEqual(g1.replace("[[feat-one|Feature One]]", "[[Feature One]]").replace("[[gap-two]]", "[[gap|gap-two]]"), before[gap_one])
        self.assertEqual(gap_two.read_text().replace("client: acme", "client: Acme"), before[gap_two])

    def test_apply_touches_only_the_flagged_link_not_copies_in_code(self):
        rel = "wiki/clients/acme/gaps/gap-one.md"
        p = self.v.root / rel
        p.write_text(p.read_text() + "\n```\n[[Feature One]] in a code sample\n```\n<!-- [[Feature One]] -->\n")
        self.v.run("apply", rel, "--root", str(self.v.root))
        text = p.read_text()
        self.assertIn("Links: [[feat-one]] and [[feat-one|Feature One]]", text)
        self.assertIn("```\n[[Feature One]] in a code sample\n```", text)
        self.assertIn("<!-- [[Feature One]] -->", text)

    def test_apply_rewrites_relation_link_inside_its_value(self):
        rel = "wiki/clients/acme/gaps/gap-two.md"
        p = self.v.root / rel
        p.write_text(p.read_text().replace("tags: alpha, gamma", 'tags: alpha, gamma\nrelated-feature: "[Feature]([[feature|feat-one]])"'))
        self.assertIn(("relation-noncanonical", "[[feature|feat-one]]"), rules(self.v.check(rel)))
        self.v.run("apply", rel, "--root", str(self.v.root))
        self.assertIn('related-feature: "[Feature]([[feat-one]])"', p.read_text())
        self.assertNotIn("relation-noncanonical", {x["rule"] for x in self.v.check(rel)})

    def test_apply_list_and_block_items(self):
        rel = "wiki/clients/acme/features/feat-one.md"
        p = self.v.root / rel
        write(p, FEAT_ONE.replace("client: acme", "client: [Acme]").replace("  - alpha", "  - alpha\n  - Alpha"))
        self.v.run("approve", "tag.alpha", "--by", "H", "--root", str(self.v.root))
        self.v.run("apply", rel, "--root", str(self.v.root))
        text = p.read_text()
        self.assertIn("client: [acme]", text)
        self.assertIn("  - alpha\n  - alpha\n", text)


class TestInitInstall(unittest.TestCase):
    def setUp(self):
        self.v = Vault()

    def tearDown(self):
        self.v.close()

    def test_init_classifies_every_observed_value(self):
        """Acceptance: every observed value classified (approved or proposed), zero unknowns."""
        res = self.v.init()
        self.assertEqual(res["unknown"], [])
        self.assertEqual(res["errors"], [])
        onto = self.v.project().onto
        st = lambda tid: onto.terms[tid]["status"]
        self.assertEqual(st("gap.severity.critical"), "approved")        # template
        self.assertEqual(st("gap.status.mitigated"), "approved")         # template wins the conflict
        self.assertNotIn("gap.status.under-review", onto.terms)          # SCHEMA-only, unobserved: reported, not adopted
        self.assertEqual(st("feature.priority.p0"), "proposed")          # observed outside the template
        self.assertEqual(onto.terms["feature.priority.p0"]["value"], "P0")
        self.assertEqual(st("client.acme"), "approved")                  # scope folder
        self.assertEqual(st("client.shared"), "approved")                # SCHEMA `{client-slug}|shared`
        self.assertEqual(onto.terms["client.shared"]["approved-by"], "declared in source")
        self.assertIn("Acme", onto.terms["client.acme"]["proposed-aliases"])
        self.assertEqual(st("tag.alpha"), "proposed")
        self.assertEqual(st("type.index"), "approved")                   # structural
        self.assertEqual(st("type.platform"), "proposed")                # no template, not in SCHEMA
        self.assertEqual(onto.terms["type.gap"].get("definition"), "A difference between the legacy platform and the target.")
        rel = onto.terms["rel.related-feature"]
        self.assertEqual((rel["status"], rel["range"], rel["domain"]), ("proposed", ["feature"], ["gap"]))
        report = json.loads((self.v.root / engine.REPORT_REL).read_text())
        self.assertIn("gap.status", [c["binding"] for c in report["conflicts"]])
        self.assertEqual(self.v.last_init[0], 0)

    def test_folder_note_title_is_a_spelling_and_field_name_states_the_range(self):
        write(self.v.root / "wiki/clients/acme/README.md", "# Acme Industries — client overview\n")
        write(self.v.root / "wiki/clients/acme/gaps/named.md", "---\ntype: gap\nclient: Acme Industries\nseverity: high\n---\n# Named\n")
        write(self.v.root / "wiki/clients/acme/gaps/wrong-range.md", '---\ntype: gap\nclient: acme\nseverity: low\nrelated-feature: "[[gap-two]]"\n---\n# W\n')
        res = self.v.init()
        onto = self.v.project().onto
        self.assertNotIn("client.acme-industries", onto.terms)
        self.assertIn("Acme Industries", onto.terms["client.acme"]["proposed-aliases"])
        self.assertEqual(onto.terms["client.acme"]["label"], "Acme Industries")
        self.assertEqual(onto.terms["rel.related-feature"]["range"], ["feature"])
        self.assertIn(("relation-range", "[[gap-two]]"), rules(self.v.check("wiki/clients/acme/gaps/wrong-range.md")))
        self.assertIn(("value-noncanonical", "Acme Industries"), rules(self.v.check("wiki/clients/acme/gaps/named.md")))
        self.assertEqual(res["unknown"], [])

    def test_decisions_override_defaults(self):
        res = self.v.init({"approve": ["tag.*", "feature.status.draft"], "deprecate": {"feature.priority.p0": "feature.priority.p1"},
                           "vocab_source": {"gap.status": "union"}, "approve_aliases": ["client.acme"],
                           "policy": {"overrides": {"tag": "strict"}}})
        onto = self.v.project().onto
        self.assertEqual(onto.terms["tag.alpha"]["status"], "approved")
        self.assertEqual(onto.terms["tag.alpha"]["approved-by"], "Test Human")
        self.assertEqual(onto.terms["feature.priority.p0"]["replaced-by"], "feature.priority.p1")
        self.assertEqual(onto.terms["gap.status.under-review"]["status"], "approved")
        self.assertIn("Acme", onto.terms["client.acme"]["aliases"])
        self.assertEqual(onto.overrides["tag"], "strict")
        self.assertEqual(res["unknown"], [])

    def test_rerun_extends_without_changing_existing_terms(self):
        self.v.init()
        self.v.run("approve", "tag.beta", "--by", "H", "--root", str(self.v.root))
        write(self.v.root / "wiki/clients/acme/gaps/gap-three.md", "---\ntype: gap\nclient: acme\nseverity: high\ntags: [delta]\n---\n# G3\n")
        res = self.v.init()
        onto = self.v.project().onto
        self.assertEqual(onto.terms["tag.beta"]["status"], "approved")
        self.assertEqual(onto.terms["tag.delta"]["status"], "proposed")
        self.assertEqual(res["added"].get("tags"), 1)

    def test_install_is_idempotent_and_preserves_existing_hooks(self):
        write(self.v.root / ".claude/settings.json", json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "mine.sh"}]}]}}))
        self.v.init()
        s1 = (self.v.root / ".claude/settings.json").read_text()
        code, out, err = self.v.run("install", "--root", str(self.v.root), "--skill-dir", str(SKILL_DIR))
        self.assertEqual(code, 0, err)
        s2 = json.loads((self.v.root / ".claude/settings.json").read_text())
        self.assertEqual(s1, (self.v.root / ".claude/settings.json").read_text())
        cmds = [h["command"] for e in s2["hooks"]["PreToolUse"] for h in e["hooks"]]
        self.assertIn("mine.sh", cmds)
        self.assertEqual(sum("ontology-guard.sh pre" in c for c in cmds), 1)
        self.assertEqual(len(s2["hooks"]["SessionStart"]), 1)
        cm = (self.v.root / "CLAUDE.md").read_text()
        self.assertIn("keep me", cm)
        self.assertEqual(cm.count(engine.SENTINEL_OPEN), 1)
        self.assertIn("wiki/_schema/ontology.yaml", cm)
        self.assertIn("not yours to fix as a side effect", cm)  # an eval baseline "fixed" pre-existing violations unasked
        self.assertTrue(os.access(self.v.root / engine.GUARD_HOOK_REL, os.X_OK))
        self.assertIn(".claude/ontology/state.json", (self.v.root / ".gitignore").read_text())

    def test_templates_carry_their_binding(self):
        self.v.init()
        gap_tpl = (self.v.root / "wiki/_schema/templates/gap.md").read_text()
        self.assertIn("severity: # gap.severity: critical|high|medium|low", gap_tpl)
        self.assertIn("client: # client.*", gap_tpl)
        self.assertIn("related-feature: # rel.related-feature → feature", gap_tpl)
        self.assertEqual(engine.parse_template_vocab("gap.severity: critical|high|medium|low"), ["critical", "high", "medium", "low"])
        mined = engine.mine_templates(self.v.root / "wiki/_schema/templates")
        self.assertEqual(mined["gap"]["vocab"]["severity"], ["critical", "high", "medium", "low"])

    def test_render_doc_sections(self):
        self.v.init()
        doc = (self.v.root / "wiki/_schema/ONTOLOGY.md").read_text()
        for needle in ("## Controlled fields", "### `gap.severity`", "## Entities", "## Relations", "## Tags", "**Proposed", "/ontology:propose"):
            self.assertIn(needle, doc)

    def test_check_changed_since_is_a_ratchet(self):
        if not shutil.which("git"):
            self.skipTest("git not available")
        self.v.init()
        r = self.v.root
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        subprocess.run(["git", "init", "-q", "."], cwd=r, check=True)
        subprocess.run(["git", "add", "-A"], cwd=r, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=r, check=True, env=env)
        code, out, _ = self.v.run("check", "--changed-since", "HEAD", "--root", str(r))
        self.assertEqual(code, 0, out)
        rel = r / "wiki/clients/acme/gaps/gap-one.md"
        rel.write_text(rel.read_text().replace("# Gap One", "# Gap One (touched)"))
        self.assertEqual(self.v.run("check", "--changed-since", "HEAD", "--root", str(r))[0], 0)
        rel.write_text(rel.read_text().replace("severity: critical", "severity: urgent"))
        code, out, _ = self.v.run("check", "--changed-since", "HEAD", "--root", str(r))
        self.assertEqual(code, 1)
        self.assertIn("urgent", out)
        self.assertNotIn("shared-name", out)  # pre-existing ambiguity is not "new"

    def test_fingerprint_includes_the_engine(self):
        self.v.init()
        proj = self.v.project()
        fake = self.v.root / "engine-copy.py"
        fake.write_text("# engine v1\n")
        saved = engine.__file__
        try:
            engine.__file__ = str(fake)
            fp1 = engine.fingerprint(proj)
            fake.write_text("# engine v2\n")
            self.assertNotEqual(fp1, engine.fingerprint(proj))
        finally:
            engine.__file__ = saved

    def test_changed_since_works_from_a_subfolder_of_the_repo(self):
        if not shutil.which("git"):
            self.skipTest("git not available")
        outer = Path(tempfile.mkdtemp(prefix="ontology-monorepo-"))
        try:
            shutil.copytree(self.v.root, outer / "apps" / "wiki project")
            sub = outer / "apps" / "wiki project"
            v = Vault.__new__(Vault)
            v.root = sub
            v.init()
            env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
            subprocess.run(["git", "init", "-q", "."], cwd=outer, check=True)
            subprocess.run(["git", "add", "-A"], cwd=outer, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=outer, check=True, env=env)
            page = sub / "wiki/clients/acme/gaps/gap-one.md"
            page.write_text(page.read_text().replace("severity: critical", "severity: urgent"))
            code, out, _ = v.run("check", "--changed-since", "HEAD", "--root", str(sub))
            self.assertEqual(code, 1, out)
            self.assertIn("urgent", out)
        finally:
            shutil.rmtree(outer, ignore_errors=True)

    def test_hook_commands_survive_a_space_in_the_project_path_and_old_entries_upgrade(self):
        if not shutil.which("bash"):
            self.skipTest("bash not available")
        spaced = Path(tempfile.mkdtemp(prefix="ontology space test-"))
        try:
            shutil.copytree(self.v.root, spaced / "my project")
            root = spaced / "my project"
            v = Vault.__new__(Vault)
            v.root = root
            write(root / ".claude/settings.json", json.dumps({"hooks": {"PreToolUse": [{"matcher": "Write|Edit|MultiEdit", "hooks": [
                {"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/ontology-guard.sh pre", "timeout": 20}]}]}}))
            v.init()
            settings = json.loads((root / ".claude/settings.json").read_text())
            pre = [h["command"] for e in settings["hooks"]["PreToolUse"] for h in e["hooks"] if "ontology-guard.sh pre" in h["command"]]
            self.assertEqual(pre, ['"$CLAUDE_PROJECT_DIR"/.claude/hooks/ontology-guard.sh pre'])
            payload = json.dumps({"tool_name": "Write", "cwd": str(root), "tool_input": {"file_path": str(root / "wiki/clients/acme/gaps/new.md"),
                                  "content": "---\ntype: gap\nclient: acme\nseverity: urgent\n---\n# N\n"}})
            p = subprocess.run(["bash", "-c", pre[0]], input=payload, capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))
            self.assertEqual(p.returncode, 2, p.stderr)
        finally:
            shutil.rmtree(spaced, ignore_errors=True)

    def test_log_updated_date_follows_new_entries(self):
        self.v.init()
        log = self.v.root / "wiki/_log.md"
        log.write_text(log.read_text().replace("type: log\n", "type: log\nupdated: 2020-01-01\n", 1))
        self.v.run("propose", "gap.severity.urgent", "--definition", "x", "--root", str(self.v.root))
        self.assertIn(f"updated: {engine.today()}", log.read_text().split("---", 2)[1])

    def test_alias_cell_and_strict_proposed_wording(self):
        self.v.init()
        doc = (self.v.root / "wiki/_schema/ONTOLOGY.md").read_text()
        self.assertNotIn("|  · proposed", doc)
        self.assertIn("| proposed: `Acme` |", doc)
        onto_file = self.v.root / "wiki/_schema/ontology.yaml"
        onto_file.write_text(onto_file.read_text().replace("proposed: warn", "proposed: strict", 1))
        v = [x for x in self.v.check("wiki/clients/acme/features/feat-one.md") if x["rule"] == "value-proposed"]
        vocab = [x for x in v if x["family"] == "vocab"]
        self.assertTrue(vocab and all(x["policy"] == "strict" and "blocked until a human approves" in x["suggestion"] for x in vocab))
        self.assertTrue(all(x["policy"] == "warn" for x in v if x["family"] == "tag"))  # the tag: warn override still wins
        code, msg = self.v.pre("Write", "wiki/clients/acme/gaps/new.md", content="---\ntype: gap\nclient: acme\nseverity: urgent\n---\n# N\n")
        self.assertEqual(code, 2)
        self.assertIn("stays blocked", msg)

    def test_status_banner_uses_cache(self):
        self.v.init()
        r = str(self.v.root)
        code, out, _ = self.v.run("status", "--banner", "--root", r)
        self.assertIn("🧭 project-ontology", out)
        self.assertIn("open violations", out)
        state = self.v.root / engine.STATE_REL
        self.assertTrue(state.exists())
        fp1 = json.loads(state.read_text())["fingerprint"]
        self.v.run("status", "--banner", "--root", r)
        self.assertEqual(json.loads(state.read_text())["fingerprint"], fp1)
        time.sleep(0.01)
        p = self.v.root / "wiki/clients/acme/gaps/gap-two.md"
        p.write_text(p.read_text() + "\nmore\n")
        self.v.run("status", "--banner", "--root", r)
        self.assertNotEqual(json.loads(state.read_text())["fingerprint"], fp1)

    def test_load_for_db_shape(self):
        self.v.init()
        d = engine.load_for_db(self.v.root)
        self.assertEqual(d["api"], engine.API_VERSION)
        ids = {t["id"] for t in d["terms"]}
        self.assertIn("gap.severity.critical", ids)
        self.assertIn({"alias": "Acme", "term_id": "client.acme", "status": "proposed"}, d["aliases"])
        self.assertEqual(d["pages"]["wiki/clients/acme/gaps/gap-one.md"]["id"], "client.acme.gap.gap-one")
        self.assertTrue(any(v["rule"] == "value-noncanonical" for v in d["violations"]))
        self.assertIsNone(engine.load_for_db(Path(tempfile.mkdtemp())))

    def test_no_wiki_project_governs_given_dirs(self):
        root = Path(tempfile.mkdtemp(prefix="ontology-nowiki-"))
        try:
            write(root / "docs/adr/0001-a.md", "---\ntype: adr\nstatus: accepted\n---\n# A\n")
            write(root / "docs/adr/0002-b.md", "---\ntype: adr\nstatus: Accepted\n---\n# B\n")
            v = Vault.__new__(Vault)
            v.root = root
            v.run("init", "--scan", "--root", str(root), "--govern", "docs/adr", "--skill-dir", str(SKILL_DIR))
            code, out, err = v.run("init", "--write", "--root", str(root), "--skill-dir", str(SKILL_DIR), "--by", "H")
            res = json.loads(out)
            self.assertEqual(res["unknown"], [])
            self.assertTrue((root / ".claude/ontology/ontology.yaml").exists())
            self.assertIn("Project Ontology", (root / "CLAUDE.md").read_text())
            self.assertIn("proposed", {t["status"] for t in engine.load_for_db(root)["terms"] if t["id"] == "type.adr"})
        finally:
            shutil.rmtree(root, ignore_errors=True)


class TestPerformance(unittest.TestCase):
    def test_vault_check_is_not_quadratic_in_broken_links(self):
        """A folder-note fallback that walked every file per broken link, plus difflib suggestions per link,
        made a 5,070-page vault take 55 s. Vault-wide sweeps now index folders and skip suggestions."""
        v = Vault()
        try:
            v.init()
            for i in range(1500):
                write(v.root / f"wiki/clients/acme/gaps/bulk-{i}.md", f"---\ntype: gap\nclient: acme\nseverity: high\n---\n# B{i}\n\n[[missing-{i}]] [[bulk-{(i + 1) % 1500}]]\n")
            t0 = time.time()
            viols, pages = engine.check_all(v.project())
            elapsed = time.time() - t0
            self.assertEqual(sum(1 for x in viols if x["rule"] == "link-broken" and x["path"].endswith(tuple(f"bulk-{i}.md" for i in range(1500)))), 1500)
            self.assertLess(elapsed, 5.0, f"check_all over 1,500 pages took {elapsed:.1f}s")
        finally:
            v.close()


class TestRealVault(unittest.TestCase):
    def test_plugin_wiki_performance_and_zero_unknowns(self):
        src = PLUGIN_ROOT / "wiki"
        if not (src / "_schema").is_dir():
            self.skipTest("plugin wiki not present")
        root = Path(tempfile.mkdtemp(prefix="ontology-plugin-wiki-"))
        try:
            shutil.copytree(src, root / "wiki")
            v = Vault.__new__(Vault)
            v.root = root
            t0 = time.time()
            res = v.init()
            self.assertEqual(res["unknown"], [])
            self.assertEqual(res["errors"], [])
            t_all = time.time()
            viols, pages = engine.check_all(engine.Project.load(root))
            self.assertLess(time.time() - t_all, 5.0)
            self.assertGreater(len(pages), 50)
            gap = next(p for p in pages if p.endswith("gaps/co-op-billing.md"))
            t_hook = time.time()
            code, _ = engine.hook_pre({"tool_name": "Edit", "cwd": str(root), "tool_input": {"file_path": str(root / gap), "old_string": "severity: critical", "new_string": "severity: urgent"}}, root)
            self.assertLess(time.time() - t_hook, 2.0)
            self.assertEqual(code, 2)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
