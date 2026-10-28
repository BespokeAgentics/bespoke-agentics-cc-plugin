#!/usr/bin/env python3
"""Tests for resolve_target.py and check_cases.py.

    python3 skills/edge-cases/scripts/test_scripts.py

Stdlib only. Builds throwaway git repositories under a temp directory; touches nothing else.
"""

from __future__ import annotations

import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import check_cases  # noqa: E402
import resolve_target  # noqa: E402
import tree_state  # noqa: E402

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.com",
    "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
}


def run_git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True, env={**os.environ, **GIT_ENV}).stdout.strip()


# --------------------------------------------------------------------------- check_cases


def case(**over) -> dict:
    base = {
        "id": "EC-01", "lens": "domain", "title": "Exactly $50 is refused",
        "given": "subtotal is exactly 50.00", "when": "SAVE10 is applied",
        "then": "10% comes off", "expected_source": "spec",
        "expected_evidence": "brief: \"orders of $50 or more\"", "decision": None,
        "current_status": "UNHANDLED", "current_evidence": "src/coupons.js:31 — uses >",
        "verification": "as-read", "severity": "high", "likelihood": "likely", "priority": "P0",
        "stems_from": "Rules: src/coupons.js:31", "test_idea": "50.00 + SAVE10 → 5.00 off", "related": [],
    }
    base.update(over)
    return base


def doc(cases: list[dict], level: str = "standard", kind: str = "feature", grounded: bool = True,
        built: bool | None = True, applied: list[str] | None = None) -> dict:
    return {
        "schema": "edge-cases/1",
        "target": {"kind": kind, "spec": "src/coupons.js", "slug": "coupons", "level": level,
                   "grounded": grounded, "built": built},
        "lenses": {"applied": applied or ["domain", "input"], "skipped": [{"id": "ux", "reason": "no UI"}]},
        "cases": cases,
        "dismissed": [],
    }


def errors_of(d: dict, filled: bool = False, final: bool = False) -> list[str]:
    return check_cases.check(d, filled=filled, final=final)[0]


class CheckCasesTest(unittest.TestCase):
    def test_valid_document_passes(self):
        self.assertEqual(errors_of(doc([case()])), [])

    def test_priority_is_computed_not_chosen(self):
        d = doc([case(priority="P2")])
        self.assertTrue(any("should be P0" in e for e in errors_of(d)))
        check_cases.fill(d)
        self.assertEqual(d["cases"][0]["priority"], "P0")
        self.assertEqual(errors_of(d), [])

    def test_matrix_corners(self):
        for sev, lik, want in [("critical", "rare", "P1"), ("high", "possible", "P1"),
                               ("medium", "likely", "P1"), ("low", "likely", "P2"), ("low", "rare", "P3")]:
            self.assertEqual(check_cases.priority_of({"severity": sev, "likelihood": lik}), want)

    def test_fill_sorts_by_priority(self):
        d = doc([case(id="EC-01", severity="low", likelihood="rare"),
                 case(id="EC-02", severity="critical", likelihood="likely", given="other")])
        check_cases.fill(d)
        self.assertEqual([c["id"] for c in d["cases"]], ["EC-02", "EC-01"])

    def test_convention_needs_location(self):
        d = doc([case(expected_source="convention", expected_evidence="the cart does this elsewhere")])
        self.assertTrue(any("convention source needs file:line" in e for e in errors_of(d)))

    def test_proposed_needs_decision_and_note(self):
        self.assertTrue(any("needs decision" in e for e in errors_of(doc([case(expected_source="proposed")]))))
        d = doc([case(expected_source="proposed", decision="decided")])
        self.assertTrue(any("needs a decision_note" in e for e in errors_of(d)))
        d = doc([case(expected_source="proposed", decision="decided", decision_note="reject it")])
        self.assertEqual(errors_of(d), [])

    def test_spec_source_rejects_decision(self):
        self.assertTrue(any("decision must be null" in e for e in errors_of(doc([case(decision="needed")]))))

    def test_code_status_needs_location(self):
        d = doc([case(current_evidence="the comparison is wrong")])
        self.assertTrue(any("UNHANDLED needs file:line" in e for e in errors_of(d)))

    def test_current_evidence_key_is_required(self):
        c = case()
        del c["current_evidence"]
        self.assertTrue(any("current_evidence is required" in e for e in errors_of(doc([c]))))

    def test_time_is_not_a_location(self):
        self.assertIsNone(check_cases.LOCATION.search("fails at 10:30 every night"))
        self.assertIsNotNone(check_cases.LOCATION.search("see Makefile:12"))
        self.assertIsNotNone(check_cases.LOCATION.search("src/a.ts:4-9"))

    def test_ungrounded_target_requires_na(self):
        d = doc([case()], kind="plan", grounded=False, built=None)
        self.assertTrue(any("must be N/A" in e for e in errors_of(d)))
        d = doc([case(current_status="N/A", current_evidence="", verification="n/a")],
                kind="plan", grounded=False, built=None)
        self.assertEqual(errors_of(d), [])

    def test_unbuilt_feature_requires_na(self):
        d = doc([case()], grounded=True, built=False)
        self.assertTrue(any("must be N/A" in e for e in errors_of(d)))

    def test_built_code_target_rejects_na(self):
        d = doc([case(current_status="N/A", current_evidence="", verification="n/a")])
        self.assertTrue(any("use UNKNOWN" in e for e in errors_of(d)))

    def test_quick_trims_to_cap(self):
        cases = [case(id=f"EC-{i:02d}", given=f"g{i}", severity="medium", likelihood="possible") for i in range(1, 15)]
        cases[13]["severity"] = "critical"
        d = doc(cases, level="quick")
        self.assertTrue(any("at most 12" in e for e in errors_of(d)))
        self.assertEqual(check_cases.fill(d), 2)
        self.assertEqual(len(d["cases"]), 12)
        self.assertEqual(d["trimmed"], 2)
        self.assertEqual(d["cases"][0]["id"], "EC-14")
        self.assertEqual(errors_of(d, filled=True), [])

    def test_interaction_rules(self):
        parents = [case(id="EC-01"), case(id="EC-02", given="other")]
        inter = case(id="EC-03", lens="interaction", given="both", related=["EC-01", "EC-02"])
        self.assertTrue(any("only at deep" in e for e in errors_of(doc(parents + [inter]))))
        d = doc([case(id="EC-01", verification="upheld"), case(id="EC-02", given="other", verification="upheld"),
                 {**inter, "verification": "upheld"}], level="deep")
        self.assertEqual(errors_of(d), [])
        d["cases"][2]["related"] = ["EC-01"]
        self.assertTrue(any("two existing case ids" in e for e in errors_of(d)))

    def test_lens_must_be_applied(self):
        d = doc([case(lens="security")])
        self.assertTrue(any("not in lenses.applied" in e for e in errors_of(d)))

    def test_verification_by_level(self):
        self.assertTrue(any("only at deep" in e for e in errors_of(doc([case(verification="upheld")]))))
        d = doc([case(verification="probe-confirmed")], level="deep")
        self.assertTrue(any("only at prove" in e for e in errors_of(d)))
        self.assertEqual(errors_of(doc([case(verification="probe-confirmed")], level="prove")), [])

    def test_final_requires_verified_p0_p1_at_deep(self):
        d = doc([case()], level="deep")
        errs, warns = check_cases.check(d, filled=False, final=False)
        self.assertEqual(errs, [])
        self.assertTrue(any("a skeptic must check it" in w for w in warns))
        self.assertTrue(any("a skeptic must check it" in e for e in errors_of(d, final=True)))

    def test_duplicates_and_ids(self):
        errs, warns = check_cases.check(doc([case(), case()]), filled=False, final=False)
        self.assertTrue(any("duplicate id" in e for e in errs))
        self.assertTrue(any("same given/when" in w for w in warns))
        self.assertTrue(any("id must look like" in e for e in errors_of(doc([case(id="7")]))))

    def test_locations_must_exist_in_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src" / "coupons.js").write_text("a\nb\nc\n")
            ok = doc([case(current_evidence="src/coupons.js:2-3 — the comparison")])
            self.assertEqual(check_cases.check_locations(ok, repo), [])
            past = doc([case(current_evidence="src/coupons.js:31 — uses >")])
            self.assertTrue(any("has 3 line(s)" in e for e in check_cases.check_locations(past, repo)))
            beyond = doc([case(current_evidence="src/coupons.js:3-4 — range past the end")])
            self.assertTrue(any("has 3 line(s)" in e for e in check_cases.check_locations(beyond, repo)))
            (repo / ".github").mkdir()
            (repo / ".github" / "ci.yml").write_text("on: push")
            dotted = doc([case(current_evidence="./.github/ci.yml:1 — no trailing newline")])
            self.assertEqual(check_cases.check_locations(dotted, repo), [])
            missing = doc([case(current_evidence="coupons.js:2 — not repo-relative")])
            self.assertTrue(any("not a file in the repo" in e for e in check_cases.check_locations(missing, repo)))
            conv = doc([case(expected_source="convention", expected_evidence="lib/cart.js:9 does this")])
            self.assertTrue(any("lib/cart.js" in e for e in check_cases.check_locations(conv, repo)))

    def test_location_keeps_line_ranges(self):
        self.assertEqual(check_cases.LOCATION.search("see src/r.js:8-10 here").group(0), "src/r.js:8-10")

    def test_dismissed_cannot_also_be_a_case(self):
        d = doc([case()])
        d["dismissed"] = [{"id": "EC-01", "title": "t", "reason": "unreachable"}]
        self.assertTrue(any("both a case and dismissed" in e for e in errors_of(d)))

    def test_markdown_marks_decisions(self):
        d = doc([case(expected_source="proposed", decision="needed", then="reject | expired")])
        table = check_cases.markdown(d)
        self.assertIn("**DECISION NEEDED**", table)
        self.assertIn("reject \\| expired", table)
        self.assertIn("UNHANDLED `src/coupons.js:31`", table)

    def test_cli_fill_writes_only_when_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "cases.json"
            bad = doc([case(current_evidence="no location")])
            p.write_text(json.dumps(bad))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(check_cases.main([str(p), "--fill"]), 1)
            self.assertEqual(json.loads(p.read_text()), bad)
            good = doc([case(priority=None)])
            p.write_text(json.dumps(good))
            out = io.StringIO()
            with redirect_stdout(out), redirect_stderr(io.StringIO()):
                self.assertEqual(check_cases.main([str(p), "--fill", "--summary"]), 0)
            self.assertEqual(json.loads(p.read_text())["cases"][0]["priority"], "P0")
            summary = json.loads(out.getvalue())
            self.assertEqual(summary["by_priority"]["P0"], 1)
            self.assertEqual(summary["defects_p0_p1"], ["EC-01"])

    def test_origin_only_and_always_on_changes(self):
        self.assertTrue(any("needs origin" in e for e in errors_of(doc([case()], kind="changes"))))
        self.assertEqual(errors_of(doc([case(origin="introduced")], kind="changes")), [])
        self.assertTrue(any("only to changes" in e for e in errors_of(doc([case(origin="introduced")]))))
        t = check_cases.tally(doc([case(origin="pre-existing")], kind="changes"))
        self.assertEqual(t["by_origin"], {"pre-existing": 1})

    def test_defects_need_an_agreed_expectation(self):
        d = doc([case(id="EC-01"),
                 case(id="EC-02", given="b", expected_source="proposed", decision="needed"),
                 case(id="EC-03", given="c", expected_source="proposed", decision="uncontested"),
                 case(id="EC-04", given="d", verification="upheld")], level="deep")
        t = check_cases.tally(d)
        self.assertEqual(t["defects_p0_p1"], ["EC-01", "EC-03", "EC-04"])
        self.assertEqual(t["undecided_unhandled_p0_p1"], ["EC-02"])
        self.assertEqual(t["verified_defects_p0_p1"], ["EC-04"])

    def test_review_contract_gaps(self):
        d = doc([case()])
        d["target"]["built"] = None
        self.assertTrue(any("settled to true or false" in e for e in errors_of(d)))
        d = doc([case()])
        d["dismissed"] = [{"id": "EC-09", "reason": "x"}]
        self.assertTrue(any("needs id, title and reason" in e for e in errors_of(d)))
        d = doc([case(id="EC-01", verification="upheld"),
                 case(id="EC-02", lens="interaction", given="i", related=["EC-01", "EC-01"], verification="upheld")],
                level="deep")
        self.assertTrue(any("two existing case ids" in e for e in errors_of(d)))
        d = doc([case(), "not a case"])
        self.assertEqual(check_cases.fill(d), 0)
        self.assertTrue(any("not an object" in e for e in errors_of(d)))
        d = doc([case(alternatives=["honor it", ""])])
        self.assertTrue(any("alternatives" in e for e in errors_of(d)))
        d = doc([case()], level="deep")
        d["target"].update(degraded_from="prove")
        self.assertTrue(any("degraded_reason" in e for e in errors_of(d)))
        d["target"]["degraded_reason"] = "plan target: no code to probe"
        d["cases"][0]["verification"] = "upheld"
        self.assertEqual(errors_of(d), [])

    def test_tally_counts(self):
        d = doc([case(), case(id="EC-02", given="x", current_status="HANDLED", severity="low", likelihood="rare")])
        t = check_cases.tally(d)
        self.assertEqual(t["by_status"]["HANDLED"], 1)
        self.assertEqual(t["by_priority"]["P3"], 1)


# --------------------------------------------------------------------------- resolve_target


class GitRepoCase(unittest.TestCase):
    """A throwaway repo: src/coupons.js, plans/gift-cards.md, NOTES.txt, one commit on main."""

    def setUp(self):
        self._env = {k: os.environ.get(k) for k in GIT_ENV}
        os.environ.update(GIT_ENV)
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        run_git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "src").mkdir()
        (self.repo / "plans").mkdir()
        (self.repo / "src" / "coupons.js").write_text("export function applyCoupon(cart) {\n  return cart;\n}\n")
        (self.repo / "plans" / "gift-cards.md").write_text("# Gift cards\n\nBrief.\n")
        (self.repo / "NOTES.txt").write_text("HEAD is where we are\n")
        run_git(self.repo, "add", "-A")
        run_git(self.repo, "commit", "-qm", "base")

    def tearDown(self):
        self.tmp.cleanup()
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v



class ResolveTargetTest(GitRepoCase):
    def resolve(self, target=None, kind="auto", base=None) -> dict:
        return resolve_target.resolve(target, kind, base, self.repo)

    def test_clean_tree_asks_with_candidates(self):
        r = self.resolve()
        self.assertEqual(r["kind"], "ask")
        specs = [c["spec"] for c in r["candidates"]]
        self.assertIn("plans/gift-cards.md", specs)
        self.assertTrue(any(c["kind"] == "changes" for c in r["candidates"]))

    def test_dirty_tree_resolves_uncommitted_with_untracked(self):
        (self.repo / "src" / "coupons.js").write_text("export function applyCoupon(cart) {\n  return null;\n}\n")
        (self.repo / "src" / "new.js").write_text("a\nb\n")
        r = self.resolve()
        self.assertEqual((r["kind"], r["changes"]["scope"], r["slug"]), ("changes", "uncommitted", "changes-uncommitted"))
        files = {f["path"]: f for f in r["changes"]["files"]}
        self.assertEqual(files["src/coupons.js"]["status"], "M")
        self.assertEqual((files["src/new.js"]["status"], files["src/new.js"]["added"]), ("?", 2))
        first = r["fingerprint"]
        (self.repo / "src" / "new.js").write_text("a\nb\nc\n")
        self.assertNotEqual(self.resolve()["fingerprint"], first)

    def test_branch_ahead_resolves_branch(self):
        run_git(self.repo, "checkout", "-q", "-b", "feat/fixed-amount")
        (self.repo / "src" / "coupons.js").write_text("export function applyCoupon(cart, amount) {}\n")
        run_git(self.repo, "commit", "-qam", "fixed amount")
        r = self.resolve()
        self.assertEqual((r["kind"], r["changes"]["scope"]), ("changes", "branch"))
        self.assertEqual(r["slug"], "changes-branch-feat-fixed-amount")
        self.assertEqual(r["changes"]["totals"]["files"], 1)
        run_git(self.repo, "checkout", "-q", "main")
        r = self.resolve("feat/fixed-amount")
        self.assertEqual((r["changes"]["scope"], r["changes"]["branch"]), ("branch", "feat/fixed-amount"))
        self.assertTrue(r["reason"].startswith("rule 10:"))
        run_git(self.repo, "checkout", "-q", "feat/fixed-amount")
        (self.repo / "NOTES.txt").write_text("uncommitted on the branch\n")
        r = self.resolve("feat/fixed-amount")
        self.assertTrue(r["reason"].startswith("rule 9:"))
        self.assertIn("NOTES.txt", [f["path"] for f in r["changes"]["files"]])

    def test_document_path_is_plan(self):
        r = self.resolve("plans/gift-cards.md")
        self.assertEqual((r["kind"], r["slug"], r["spec"]), ("plan", "plans-gift-cards", "plans/gift-cards.md"))

    def test_same_named_docs_get_different_slugs(self):
        for d in ("a", "b"):
            (self.repo / "docs" / d).mkdir(parents=True)
            (self.repo / "docs" / d / "plan.md").write_text(d)
        self.assertNotEqual(self.resolve("docs/a/plan.md")["slug"], self.resolve("docs/b/plan.md")["slug"])

    def test_own_output_is_invisible(self):
        # Review finding 1: one run's report made the next run's clean tree look dirty.
        for rel in (".edge-cases/x/target.json", "reviews/edge-cases/x-edge-cases.md", "out/r.md"):
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text("{}")
        r = resolve_target.resolve(None, "auto", None, self.repo, ["out/"])
        self.assertEqual(r["kind"], "ask")
        (self.repo / "src" / "coupons.js").write_text("changed\n")
        r = resolve_target.resolve(None, "auto", None, self.repo, ["out"])
        self.assertEqual([f["path"] for f in r["changes"]["files"]], ["src/coupons.js"])
        fp = r["fingerprint"]
        (self.repo / ".edge-cases" / "x" / "cases.json").write_text("[]")
        self.assertEqual(resolve_target.resolve(None, "auto", None, self.repo, ["out"])["fingerprint"], fp)

    def test_diff_cmd_runs_and_matches_files(self):
        # Review finding 15: an abbreviated empty-tree hash does not resolve.
        for target in ("HEAD", None):
            if target is None:
                (self.repo / "src" / "coupons.js").write_text("changed\n")
            r = self.resolve(target) if target else self.resolve()
            out = subprocess.run(r["changes"]["diff_cmd"].replace("git ", f"git -C {self.repo} ", 1),
                                 shell=True, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("src/coupons.js", out.stdout)

    def test_word_only_in_docs_is_not_a_built_feature(self):
        (self.repo / "plans" / "gift-cards.md").write_text("# Giftwrap\n\nWe will add giftwrap.\n")
        r = self.resolve("giftwrap")
        self.assertEqual((r["kind"], r["built"]), ("feature", None))

    def test_source_path_is_built_feature(self):
        r = self.resolve("src/coupons.js")
        self.assertEqual((r["kind"], r["built"], r["slug"]), ("feature", True, "src-coupons"))

    def test_symbol_is_feature_with_matches(self):
        r = self.resolve("applyCoupon")
        self.assertEqual((r["kind"], r["built"]), ("feature", True))
        self.assertTrue(r["matches"][0].startswith("src/coupons.js:1:"))

    def test_description_is_unknown_feature(self):
        r = self.resolve("the gift card checkout flow")
        self.assertEqual((r["kind"], r["built"], r["slug"]), ("feature", None, "the-gift-card-checkout-flow"))
        self.assertTrue(r["reason"].startswith("rule 13:"))

    def test_commit_and_range(self):
        (self.repo / "src" / "coupons.js").write_text("changed\n")
        run_git(self.repo, "commit", "-qam", "second")
        sha = run_git(self.repo, "rev-parse", "--short", "HEAD")
        r = self.resolve(sha)
        self.assertEqual((r["kind"], r["changes"]["scope"]), ("changes", "commit"))
        self.assertEqual(r["changes"]["totals"]["files"], 1)
        r = self.resolve("HEAD~1..HEAD")
        self.assertEqual((r["changes"]["scope"], r["changes"]["totals"]["files"]), ("range", 1))

    def test_head_is_a_commit_not_a_symbol(self):
        r = self.resolve("HEAD")
        self.assertEqual((r["kind"], r["changes"]["scope"]), ("changes", "commit"))
        self.assertTrue(r["reason"].startswith("rule 11:"))

    def test_root_commit_diffs_against_empty_tree(self):
        r = self.resolve("HEAD")
        self.assertEqual(r["changes"]["base"], resolve_target.EMPTY_TREE)
        self.assertEqual(r["changes"]["totals"]["files"], 3)

    def test_ref_that_is_also_a_symbol_asks(self):
        run_git(self.repo, "branch", "applyCoupon")
        r = self.resolve("applyCoupon")
        self.assertEqual(r["kind"], "ask")
        self.assertEqual({c["kind"] for c in r["candidates"]}, {"changes", "feature"})

    def test_explicit_changes_on_clean_tree_is_empty(self):
        r = self.resolve(kind="changes")
        self.assertEqual(r["changes"]["totals"]["files"], 0)
        self.assertTrue(any("empty change set" in n for n in r["notes"]))

    def test_staged_scope(self):
        (self.repo / "src" / "coupons.js").write_text("staged\n")
        run_git(self.repo, "add", "src/coupons.js")
        (self.repo / "plans" / "gift-cards.md").write_text("unstaged edit\n")
        r = self.resolve("staged")
        self.assertEqual([f["path"] for f in r["changes"]["files"]], ["src/coupons.js"])

    def test_bad_inputs_raise(self):
        with self.assertRaises(resolve_target.InputError):
            self.resolve("plans/missing.md", kind="plan")
        with self.assertRaises(resolve_target.InputError):
            self.resolve("not-a-ref", kind="changes")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(resolve_target.main(["--target", "plan", "nope.md", "--repo", str(self.repo)]), 2)

    def test_changes_outside_git_fails(self):
        plain = Path(self.tmp.name) / "plain"
        plain.mkdir()
        with self.assertRaises(resolve_target.InputError):
            resolve_target.resolve("uncommitted", "auto", None, plain)
        r = resolve_target.resolve(None, "auto", None, plain)
        self.assertEqual(r["kind"], "ask")

    def test_plan_fingerprint_tracks_content(self):
        first = self.resolve("plans/gift-cards.md")["fingerprint"]
        (self.repo / "plans" / "gift-cards.md").write_text("# Gift cards\n\nEdited.\n")
        self.assertNotEqual(self.resolve("plans/gift-cards.md")["fingerprint"], first)

    def test_cli_prints_json(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(resolve_target.main(["src/coupons.js", "--repo", str(self.repo)]), 0)
        self.assertEqual(json.loads(out.getvalue())["kind"], "feature")


class TreeStateTest(GitRepoCase):
    """Review finding 8: `git status --porcelain` cannot prove a run was read-only."""

    def snap(self, *excludes):
        return tree_state.snapshot(self.repo, list(excludes))

    def test_untouched_tree_is_unchanged(self):
        (self.repo / "src" / "coupons.js").write_text("dirty before the run\n")
        before = self.snap()
        self.assertEqual(tree_state.compare(before, self.snap()), [])

    def test_already_dirty_file_edited_again_is_caught(self):
        (self.repo / "src" / "coupons.js").write_text("dirty before the run\n")
        before = self.snap()
        (self.repo / "src" / "coupons.js").write_text("edited during the run\n")
        self.assertEqual(tree_state.compare(before, self.snap()), ["modified again during the run: src/coupons.js"])

    def test_leftover_probe_inside_untracked_dir_is_caught(self):
        (self.repo / "test").mkdir()
        (self.repo / "test" / "new.test.js").write_text("untracked before\n")
        before = self.snap()
        probe = self.repo / "test" / "coupons.edge-probe.test.js"
        probe.write_text("probe")
        self.assertEqual(tree_state.compare(before, self.snap()),
                         ["changed during the run: test/coupons.edge-probe.test.js"])
        probe.unlink()
        self.assertEqual(tree_state.compare(before, self.snap()), [])

    def test_own_output_and_excludes_are_ignored(self):
        before = self.snap("wiki")
        for rel in (".edge-cases/s/cases.json", "reviews/edge-cases/s.md", "wiki/_log.md"):
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text("x")
        self.assertEqual(tree_state.compare(before, self.snap("wiki")), [])
        self.assertEqual(tree_state.compare(before, self.snap()), ["changed during the run: wiki/_log.md"])

    def test_cli_compare_exit_codes(self):
        snap = Path(self.tmp.name) / "before.json"
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(tree_state.main(["snapshot", "--repo", str(self.repo)]), 0)
        snap.write_text(out.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(tree_state.main(["compare", str(snap), "--repo", str(self.repo)]), 0)
            (self.repo / "NOTES.txt").write_text("edited")
            self.assertEqual(tree_state.main(["compare", str(snap), "--repo", str(self.repo)]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
