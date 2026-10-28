# Phases 1–2 — Lens analysts and consolidation

## The case shape

Every case, from every analyst, has this shape (`assets/templates/case.schema.json` is the contract,
`scripts/check_cases.py` enforces it):

```json
{
  "id": "EC-07",
  "lens": "domain",
  "title": "Order of exactly $50.00 is refused the coupon",
  "given": "SAVE10 requires a $50 minimum; the cart subtotal is exactly 50.00",
  "when": "the shopper applies SAVE10",
  "then": "the coupon applies and 10% is taken off",
  "expected_source": "spec",
  "expected_evidence": "brief §Rules: \"orders of $50 or more qualify\"",
  "decision": null,
  "current_status": "UNHANDLED",
  "current_evidence": "src/coupons.js:21 — `subtotal > coupon.minSubtotal` excludes 50.00",
  "verification": "as-read",
  "severity": "high",
  "likelihood": "likely",
  "priority": "P0",
  "stems_from": "Rules and thresholds: src/coupons.js:21 minSubtotal comparison",
  "test_idea": "cart subtotal 50.00 + SAVE10 → discount 5.00",
  "related": []
}
```

Field rules:

- **`given` / `when` / `then`** — concrete and observable. `then` describes what a user, caller, or
  database sees, not an implementation ("shows 'Code expired on 3 Oct'", not "handles the error").
- **`expected_source`** — where `then` comes from:
  - `spec` — a document, ticket, or wiki page states it, or a requirement is written in the code's own
    comments or docstrings (`// Orders of $50 or more qualify`). `expected_evidence` quotes it, with
    `file:line` when the source is a code comment.
  - `convention` — this codebase already behaves this way in an equivalent place. `expected_evidence`
    is that `file:line`.
  - `proposed` — you are proposing it. `expected_evidence` is the one-line rationale, and `decision`
    is set:
    - `uncontested` — any reasonable product would do this (don't crash on an empty list, don't
      charge twice). No question needed.
    - `needed` — reasonable products differ (honor an expired coupon already in the cart, or reject it?).
      Goes to the interview.
    - `decided` / `open` — set in Phase 3 only, with `decision_note` holding the answer.
    - `alternatives` (optional) — the other behaviors a product could reasonably choose. Phase 3 offers
      them as options, and the report shows them for cases that stay undecided.
  - `decision` is `null` for `spec` and `convention`.
- **`current_status`** — code targets only (`N/A` when not grounded or not built):
  - `HANDLED` — the code produces `then`. Cite where.
  - `PARTIAL` — the code handles part of it (validates on the client but not the server; handles it
    on create but not on update). Cite both halves.
  - `UNHANDLED` — the code does something else (crashes, wrong result, silent no-op). Cite the place
    that does the wrong thing.
  - `UNKNOWN` — you could not determine it. Say why in `current_evidence`. This is an honest result,
    not a failure.
- **`verification`** — `as-read` from analysts; later phases set `upheld`, `overturned`,
  `probe-confirmed`, `probe-not-reproduced`, `probe-inconclusive`. Use `n/a` when status is `N/A`.
- **`stems_from`** — the `surface.md` element this case comes from. A case that stems from nothing on
  the surface is filler; drop it.
- **`origin`** — changes targets only, and required there: `introduced` when the diff made the case
  reachable or broke its handling (the new FIVEOFF path, a caller the change invalidated);
  `pre-existing` when the same behavior exists at the base. Pre-existing cases are still reported in
  full — knowing the change did not cause a defect does not make it less of a defect. Omit `origin` for
  plan and feature targets.
- **`priority`** — leave it out or `null`; `check_cases.py --fill` computes it.

## Severity and likelihood

Score them separately. Severity is how bad it is **if it happens and is mishandled**. Likelihood is how
often real users or systems reach the condition. Do not raise one because the other is high.

| Severity | Meaning |
| --- | --- |
| `critical` | Data loss or corruption, a security or privacy breach, money computed or moved wrongly, a legal/compliance violation, or the flow unusable for everyone who hits it |
| `high` | The user is blocked or gets a wrong result with no workaround, or a silent wrong output (they believe it worked) |
| `medium` | Degraded but recoverable: a confusing error, a retry needed, a workaround exists |
| `low` | Cosmetic or a minor annoyance |

| Likelihood | Meaning |
| --- | --- |
| `likely` | Happens in normal use: double-click, empty list, pasted whitespace, back button, slow network, a value exactly at a round-number threshold |
| `possible` | Needs an uncommon but legitimate condition: concurrent edits, session expiry mid-flow, 10,000 items, a DST night. Security cases on an exposed surface are at least `possible` |
| `rare` | Needs an unusual combination of conditions |

**Priority** is computed by `check_cases.py` from this matrix:

| | likely | possible | rare |
| --- | --- | --- | --- |
| **critical** | P0 | P0 | P1 |
| **high** | P0 | P1 | P2 |
| **medium** | P1 | P2 | P3 |
| **low** | P2 | P3 | P3 |

## Analyst prompt (standard and above)

Launch one `general-purpose` agent per applicable lens, all in one response. Substitute every
`{variable}` before sending.

```
You are the {LENS_NAME} analyst in an edge-case analysis.

Target: {kind} `{spec}` (built: {built}, grounded: {grounded}). Level: {level}.
Focus: {focus or "none"}.

Read first:
- {WORK_DIR}/surface.md — the surface map. Every case must stem from an element of it.
- {target material: the document at {path} | the diff from `{diff_cmd}` | the files under {paths}}
- The checklist for your lens, below. It is a prompt for looking, not a list to transcribe.

{paste the lens section from references/taxonomy.md}

Produce cases ONLY for the {lens} lens. For each case:
- given / when / then: a concrete trigger and an observable outcome. Not a category.
- expected_source: spec (quote the document) | convention (file:line where this codebase already
  does it) | proposed (one-line rationale, decision: uncontested | needed).
- {if grounded and built} current_status HANDLED | PARTIAL | UNHANDLED | UNKNOWN with
  current_evidence "path:line — what the code does", with the path relative to the repo root.
  Read the code; do not infer from names.
  If you cannot find it, the status is UNKNOWN. Never invent a location.
  {else} current_status "N/A", verification "n/a".
- verification: "as-read".
- severity and likelihood from the rubric below, scored separately. Leave priority null.
- stems_from: the surface.md element. test_idea: one line.
- {changes targets only} origin: introduced (the diff caused it) | pre-existing (the base already
  behaves this way). Check the base with `git show {base}:<path>` before choosing.
- id: "{LENS_PREFIX}-1", "{LENS_PREFIX}-2", ... where LENS_PREFIX is the lens id in capitals
  (INPUT-1, DOMAIN-2). The orchestrator renumbers.

{paste the severity and likelihood tables}

Do not pad. Two real cases beat ten generic ones. Skip a checklist item the surface cannot reach,
and list it in skipped_checks with the reason.

Write {WORK_DIR}/lenses/{lens}.json:
{"lens": "{lens}", "cases": [...], "skipped_checks": ["item — why it does not apply"]}
Then reply with one line: the number of cases and the highest severity.
```

A shared analyst (more than eight lenses applied) gets the checklists for both of its lenses, keeps
each case in the lens where its fix lives, and writes one file per lens.

At `quick` there are no analysts: apply the same rules yourself to the 3–4 chosen lenses.

## Consolidation

After every analyst has returned:

1. **Load** all `lenses/*.json`. Check that each case's `stems_from` names something real in
   `surface.md`. Drop any that do not, and record the count as `dropped` in `cases.json`; the report's
   Coverage section states it.
2. **Merge duplicates.** Two cases are the same when they share the trigger and the fix would live in
   the same place (a missing `trim()` found by both `input` and `ux`). Keep the sharpest wording, keep
   the lens where the fix lives, union the evidence, and keep the higher severity only if the evidence
   supports it.
3. **Reconcile conflicts.** If two analysts gave the same case different statuses, re-read the cited
   lines yourself and pick the one the code supports. If you still cannot tell, use `UNKNOWN`.
4. **Number** the survivors `EC-01`, `EC-02`, … in any order. IDs are stable from here on; later
   phases refer to them.
5. **Write** `{WORK_DIR}/cases.json`:

   ```json
   {
     "schema": "edge-cases/1",
     "target": {"kind": "...", "spec": "...", "slug": "...", "level": "...", "grounded": true, "built": true},
     // when prove degraded: "level": "deep", "degraded_from": "prove", "degraded_reason": "..."
     "lenses": {"applied": ["input", "domain"], "skipped": [{"id": "ux", "reason": "no UI"}]},
     "dropped": 0,
     "cases": [ ... ],
     "dismissed": []
   }
   ```

6. **Check and fill:** `python3 {SKILL_DIR}/scripts/check_cases.py {WORK_DIR}/cases.json --fill --repo {PROJECT_DIR}`.
   `--fill` computes every priority and sorts the cases. At `quick` it also keeps only the 12
   highest-priority cases (ties: severity, then likelihood, then id) and records how many it cut in
   `trimmed`, which the report's Coverage section states. Fix every error it reports and re-run until
   it exits 0.
