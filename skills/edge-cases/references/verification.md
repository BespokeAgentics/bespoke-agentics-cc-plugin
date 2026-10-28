# Phases 4 and 5 — Verification and probes

`deep` and `prove` only, and always **after** Phase 3. An analyst reading code reports what it
believes. These phases test that belief against expectations that are already settled, before the
report states it.

## Skeptics

**Who gets attacked:** every P0 and P1 case whose `current_status` is `HANDLED`, `PARTIAL`, or
`UNHANDLED` and whose `verification` is still `as-read`. Both directions matter: a wrong `HANDLED` hides
a defect, and a wrong `UNHANDLED` sends someone to fix working code.

**Batching:** group the cases by the file their evidence cites, up to five cases per skeptic. Launch
at most eight skeptics per wave (`general-purpose`, all in one response). Run further waves until every
selected case has a verdict. Forty cases is five waves; none is left `as-read`, because
`check_cases.py --final` rejects an unverified P0/P1 status at these levels.

```
You are a skeptic checking claims about how code behaves. For each case below, try to REFUTE the
stated current_status by reading the code. Do not trust the cited evidence; trace the path yourself.

- If the status is UNHANDLED or PARTIAL: look for the code path that DOES produce the expected
  outcome — a validator elsewhere, middleware, a database constraint, a caller that pre-filters,
  a framework default.
- If the status is HANDLED: look for the path that ESCAPES the handling — another entry point, an
  update path, a bulk path, a caller that bypasses the check, a branch the guard does not cover.

Cases (id, given/when/then, current_status, current_evidence):
{cases}

Repository: {PROJECT_DIR}. Surface map: {WORK_DIR}/surface.md. Cite paths relative to the repo root.

For each case return:
{"id": "...", "verdict": "upheld | overturned | unknown",
 "new_status": "<only if overturned>", "evidence": "path:line — what you found",
 "reasoning": "one or two sentences"}
Overturn only with a cited location. "I could not find the guard" upholds an UNHANDLED claim;
it does not overturn a HANDLED one.
```

Append every verdict to `{WORK_DIR}/skeptics.json` as it arrives, so a resumed run does not repeat it.

**Applying verdicts:**

| Verdict | `current_status` | `verification` | `current_evidence` |
| --- | --- | --- | --- |
| `upheld` | unchanged | `upheld` | append the skeptic's evidence when it adds a location |
| `overturned` | `new_status` | `overturned` | replace with the skeptic's evidence; keep the original as "analyst read: …" |
| `unknown` | `UNKNOWN` | `as-read` | append the skeptic's reasoning; Coverage counts it from `skeptics.json` |

Re-run `check_cases.py --fill --repo {PROJECT_DIR}`. A changed status does not change severity or
likelihood, so priorities stay stable.

## Interactions

Skip this step if `cases.json` already holds `interaction` cases (a resumed run). Otherwise launch one
`general-purpose` agent after the skeptics have returned. Give it `cases.json` (dismissed cases are
already gone) and `surface.md`.

```
You find combined-condition edge cases. From the cases in {WORK_DIR}/cases.json, look for PAIRS of
conditions that can occur together in this system and produce an outcome NEITHER produces alone.
Examples of the pattern: expired coupon + currency conversion; offline + double-submit; role
downgrade during a multi-step wizard.

Keep a pair only if you can state the different outcome concretely. Do not list pairs that just add
two independent failures together. Return at most {N} cases (N = 5 at deep, 8 at prove).

Each case uses the full case shape from {SKILL_DIR}/references/analysts.md, with:
- lens "interaction", related: [the two parent ids], stems_from: "interaction of EC-a and EC-b"
- given / when / then for the combination; test_idea in one line
- expected_source spec | convention | proposed, with the same evidence rules as any case; a proposed
  behavior that is a product decision gets decision "needed" (it stays DECISION NEEDED: the
  interview is over)
- {if grounded and built} current_status with a repo-relative path:line, or UNKNOWN; verification
  "as-read"   {else} current_status "N/A", verification "n/a"
- {changes targets} origin: introduced | pre-existing
- severity and likelihood for the combination (usually rarer than either parent); priority null
```

Merge them into `cases.json` with fresh ids, then run one more skeptic wave for any interaction case
that is P0/P1 with a code status.

## Walkthroughs

Write 3–5 scenario walkthroughs yourself, in the main session, to `{WORK_DIR}/walkthroughs.md`. Each
one is a short, realistic journey of one actor (persona, goal, five to ten steps) that passes through
several cases in order and cites their ids. Pick journeys that between them cover the P0/P1 cases.
They are for readers who will not read the matrix (QA, product, stakeholders), so write them in plain
language.

```markdown
### W1 — Returning customer, coupon from last month's email
Priya opens the promo email from 28 days ago and pastes `SAVE10 ` into the coupon field (EC-04)…
```

## Test skeletons

For every P0/P1 case, write a test skeleton to `{WORK_DIR}/skeletons.md`, in the repository's own
test framework and idiom: find an existing test file and match it. Skeletons go into the report's
appendix, never into the repo. Each one asserts `then`, names the case id, and uses the project's
existing fixtures and helpers rather than new ones. For plan targets and unbuilt features, write them
as framework-neutral Given/When/Then checklists instead.

## Runner discovery (prove)

Discover the test command from the repo itself; never invent one. Look in this order and stop at the
first that applies:

1. `package.json` `scripts.test` (and the runner it calls: vitest, jest, mocha, `node --test`, bun).
2. `pyproject.toml` / `pytest.ini` / `setup.cfg` (pytest) or `tox.ini`.
3. `Cargo.toml` (`cargo test`), `go.mod` (`go test ./...`), `*.csproj` (`dotnet test`),
   `Gemfile` + `spec/` (rspec), `mix.exs` (`mix test`).
4. `Makefile` / `justfile` `test` target.

From the runner, determine (a) the file-name pattern it discovers and (b) how to run **one file**
(`npx vitest run <file>`, `node --test <file>`, `pytest <file>`, `go test -run <Name> ./pkg`). If you
cannot determine how to run a single file, degrade to `deep`. Never run the whole suite as a probe.

## Probes (prove)

**Selection:** every P0 and P1 case that is still `UNHANDLED` or `PARTIAL` after the skeptics, whose
expectation is agreed (`expected_source` `spec` or `convention`, or `decision` `uncontested` or
`decided`), and that has no probe verdict yet. Cap: 12, by priority then id. Cases that need a real
external service, a real payment, real email, or production data are not probed; mark them
`probe-inconclusive` with the reason. Undecided cases are never probed: there is nothing agreed to
assert.

**Gate.** Before writing anything, ask with AskUserQuestion, even under `--no-interview`. Show:

- the cases to probe (id and title);
- the directory each probe file goes in;
- the exact command per file.

Options: **Run the probes (Recommended)** · **Pick which cases** (follow up with a multiSelect) ·
**Skip probes** (verdicts stay as the skeptics left them, and the report says probes were declined).

**Writing.** For each probe:

1. Add it to `{WORK_DIR}/probes/manifest.json` **before** creating the file, so cleanup works even if
   the run is interrupted (pre-flight step 5 reads it):

   ```json
   {"probes": [{"path": "test/coupons.edge-probe.test.js", "cases": ["EC-03", "EC-05"]}]}
   ```

2. Name it so the runner discovers it and nobody mistakes it for a real test:
   `<module>.edge-probe.test.<ext>`, `test_edge_probe_<module>.py`, `edge_probe_<module>_test.go`.
   Place it next to an existing test of the same module. If the module has none, put it in the
   directory the runner discovers (`test/`, `tests/`, `__tests__/`, or beside the module for Go).
3. One test per case, named with the case id, asserting **`then`** (the agreed expected behavior).
   Use the repo's existing fixtures and mocks for every dependency; never call a real network service.
4. Keep a copy of the source in `{WORK_DIR}/probes/`. The report's appendix quotes it.

**Running.** Run each probe file alone with the single-file command, with a timeout of 120 seconds and
with coverage and snapshot-writing turned off where the runner allows it. Read the output; do not
trust the exit code alone.

| Outcome | Verdict | Case update |
| --- | --- | --- |
| The assertion on `then` fails | `probe-confirmed` | Status stays `UNHANDLED`/`PARTIAL`. **Append** `probe: <assertion message>` to `current_evidence`, keeping the code `file:line`. |
| The test passes | `probe-not-reproduced` | Status becomes `HANDLED`. Replace `current_evidence` with the code `file:line` that produced `then`, followed by `probe: passed`. Say in Coverage what the analyst and skeptic missed. |
| Setup error, import error, timeout, crash before the assertion | `probe-inconclusive` | Status unchanged; the error goes into Coverage. One fix attempt is allowed for an obvious probe bug (a wrong import path). After that it stays inconclusive. |

Probe files are deleted before the report, so `current_evidence` must never cite a probe's own
`path:line`, as stack traces do: `check_cases.py --repo` would reject it. Cite the code under test.
The probe source lives on in `{WORK_DIR}/probes/` and the report appendix.

**Cleanup.** Delete every file in the manifest. Then run `tree_state.py compare` against
`tree-before.json`:

- A difference whose path contains `edge-probe` (a snapshot or cache the probe left) is the probe's
  own output: delete it and compare again.
- Any other difference is reported to the user before the report is written. Do not delete a file you
  did not create.

The phase line in the final summary shows `probes removed ✓` only after the comparison is clean.
