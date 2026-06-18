# Knowledge Loop — Algorithm & Data Model

The canonical spec for how facts, hypotheses, and rules are written, counted, promoted, and
demoted. `extract` and `promote` MUST follow this. The whole point is that `rules.md` stays
trustworthy enough to **apply by default** — so the evidence bar is strict and counters cannot
be gamed.

## 1. Entry IDs

Every entry has a stable ID, unique within its domain, so it can be referenced as it moves
between layers (a hypothesis keeps its ID when promoted to a rule).

```
<domain>-<layer-prefix>-<nnn>
```

- layer-prefix: `F` facts, `H` hypotheses, `R` rules.
- `nnn`: zero-padded sequence, monotonic per domain+layer (never reused, even after deletion).
- On promotion H→R, mint a new `R` id and record `from: <H-id>` so history is traceable.
  On demotion R→H, mint a new `H` id and record `from: <R-id>`.

Example: `pricing-H-007` → promoted → `pricing-R-003` (`from: pricing-H-007`).

## 2. Entry shapes

Entries are Markdown sections under the layer file's `## Entries` heading. Keep them compact.

**Fact (`knowledge.md`)**
```markdown
### pricing-F-012 — Enterprise deals over $50k always route through procurement
- observed: 2026-06-09
- source: [[meeting-2026-06-09-acme-pricing]]
- tags: pricing, procurement, enterprise
```

**Hypothesis (`hypotheses.md`)**
```markdown
### pricing-H-007 — Discounts above 20% require VP sign-off
- status: open            # open | promoting | demoted
- confirmations: 2
- contradictions: 0
- applies-when: any deal with a requested discount > 20%
- opened: 2026-05-20
- updated: 2026-06-09
- evidence:
  - +1 2026-05-20 [[meeting-2026-05-20-globex]] — VP approved a 25% discount
  - +1 2026-06-09 [[deal-acme-renewal]] — 22% discount escalated to VP
- tags: pricing, approvals
```

**Rule (`rules.md`)**
```markdown
### pricing-R-003 — Discounts above 20% require VP sign-off  (apply by default)
- from: pricing-H-007
- confirmations: 3
- contradictions: 0
- applies-when: any deal with a requested discount > 20%
- promoted-on: 2026-06-15
- wiki-page:            # set by /knowledge:promote, e.g. [[discount-approval-threshold]]
- evidence:
  - +1 2026-05-20 [[meeting-2026-05-20-globex]]
  - +1 2026-06-09 [[deal-acme-renewal]]
  - +1 2026-06-15 [[deal-initech-expansion]]
- tags: pricing, approvals
```

`applies-when` is mandatory on hypotheses and rules — it is the trigger `review` matches against
the current task to decide what to surface and what is testable today.

## 3. Counter integrity (non-negotiable)

A counter (`confirmations` or `contradictions`) may be incremented **at most once per distinct
source**. This is what stops the same meeting from being cited three times to fabricate a rule.

- A "source" is a linkable artifact: a wiki page (`[[meeting-…]]`, `[[decision-…]]`), a commit
  SHA, a PR, a ticket, a transcript, or a dated task. Free-text with no link is **not** a valid
  source and cannot move a counter.
- Before incrementing, scan the entry's `evidence:` list. If the source already appears, do
  **not** increment — instead note "already counted" and stop.
- `confirmations` MUST equal the number of distinct `+1` evidence bullets; `contradictions` MUST
  equal the number of distinct `-1` bullets. `audit` flags any entry where the number and the
  bullets disagree.
- Each evidence bullet format: `+1 <YYYY-MM-DD> <link> — <one-line reason>` (or `-1` for a
  contradiction).

## 4. Promotion (hypothesis → rule)

Trigger during `extract`, evaluated after counters are updated.

**Promotion bar (default):** `confirmations ≥ 3` from distinct sources **AND** `contradictions = 0`.

When met:
1. Mint an `R` id, write the rule into `rules.md` with `from:` the hypothesis id, carry the full
   evidence trail, set `promoted-on` to today, leave `wiki-page:` empty.
2. Set the hypothesis `status: promoting` and remove it from the active hypotheses list (move it
   under a `## Promoted` footer in `hypotheses.md` so history is preserved, or delete and rely on
   the rule's `from:` — pick one and be consistent; default: keep under `## Promoted`).
3. Recommend `/knowledge:promote` to create the wiki page.

**Tunable:** the bar can be raised per domain via a `promotion-threshold:` field in the domain's
`rules.md` frontmatter (e.g., a high-stakes domain may require 5). Never lower below 3 silently.

**Near-miss:** a hypothesis with `confirmations = 2, contradictions = 0` is a *promotion
candidate* — `review` and `audit` surface it so the next relevant task can close it out.

## 5. Demotion (rule → hypothesis)

Trigger during `extract` whenever new evidence contradicts a rule.

1. Record the contradicting source as a `-1` evidence bullet on the rule and increment
   `contradictions`.
2. **Any** `contradictions ≥ 1` on a rule triggers demotion (rules are "apply by default" — a
   single solid contradiction means it is no longer safe to apply blindly). Mint an `H` id, move
   the entry to `hypotheses.md` with `status: demoted`, `from:` the rule id, carrying both
   counters and the full evidence trail.
3. If the rule had a `wiki-page:`, open that wiki page, set its `status: revisited`, add a note
   describing the contradiction, and log it. Do **not** delete the wiki page — demotion is a
   status change, not erasure.
4. A demoted hypothesis can be re-promoted later, but only by clearing the contradiction (new
   distinct evidence that resolves it) and reaching the bar again. Re-promotion mints a fresh `R`
   id; the `from:` chain preserves the round trip.

## 6. Conflict & dedup handling

- **Duplicate insight:** before opening a new hypothesis, search the domain for a semantically
  equivalent one. If found, increment it (subject to §3) instead of creating a duplicate.
- **Contradictory hypotheses:** if two open hypotheses directly conflict, link them with
  `conflicts-with:` and let evidence adjudicate; never promote either while the conflict is open.
- **Cross-domain insight:** if an insight spans domains, file the fact in the most specific
  domain and add `related:` links to the others rather than duplicating the entry.

## 7. Invariants `audit` checks

1. `confirmations` == count of distinct `+1` bullets; `contradictions` == count of distinct `-1`.
2. No source appears twice in one entry's evidence.
3. Every rule has `confirmations ≥` its domain threshold and `contradictions = 0` (else it should
   have been demoted).
4. Every hypothesis and rule has a non-empty `applies-when`.
5. Every `from:` points to a real prior-layer id.
6. Every `[[link]]` and `related:` resolves.
7. `INDEX.md` counts match the files.
