# Directions — tiers, honesty contracts, and the round that gates the build

Read before Phase 2. Directions are pitched and selected BEFORE any pane is
authored: building a variant nobody wants costs an hour; a brief costs a
paragraph. The directions round is what keeps the gallery three panes the user
chose rather than three panes the model felt like making.

## The three tiers

Each tier is a *contract about what may change*, not a quality level. A gallery
that spans all three shows the user the whole ambition range in one screen —
that is the product.

| Tier | Must preserve | Must change | Mechanical proxy (checked before the interview opens) |
|---|---|---|---|
| **Restyle** | DOM tree, reading order, text inventory | Visual treatment only — density, hierarchy, emphasis, spacing | Heading/landmark/focusable sequence of the pane ≡ Current's; text-node multiset ≡ Current's |
| **Restructure** | Content inventory (same labels, same data set) | Grouping, order, information architecture | Text multiset ≈ Current's; band count/order differs; zone map differs |
| **Rethink** | The user's task and the data domain | The interaction model itself | Affordance inventory differs (e.g. table → cards + drawer); ≥1 new trigger→effect pair exists |

**"A Rethink that is secretly a restyle" is a named defect class.** If a pane's
proxy matches a lower tier's contract, demote it honestly or rebuild it —
shipping it as a Rethink teaches the user the tiers mean nothing. Run the
proxies with `__wf.focusables('#rv-<id>')`, the pane's zone map, and a text
comparison; note the result in the gallery-checks table.

Brand-faithfulness cuts across all tiers: variants consume only REPLACE 1
tokens. A direction that *requires* leaving the design system is a legitimate
pitch — but its brief must say so, and the interview must approve it before it
is built.

## Direction-brief format

Pitch **two briefs per active tier** (six by default). Keep every brief the
same width so differences read as structural, not presentational.

```markdown
### R2 — "Ledger" · tier: Restructure
**Thesis:** <one sentence — the bet this direction makes>
**Changes:** <2–4 bullets, concrete: "status column becomes row-group headers">
**Preserves:** <content/labels/hierarchy that stay — the brand-faithful anchor>
**Grounded in:** <real tokens/labels/patterns it builds from, path each>
**Risk:** <the main way this could be worse than Current>
<ASCII preview — real labels from grounding, same width as sibling briefs>
```

The thesis is the load-bearing line: it is what the user compares, what the
pane is judged against in critique rounds, and what the spec's rationale quotes.
A brief whose thesis restates the tier ("make it look better") is not a pitch.

## The directions round

One `AskUserQuestion` round, one question per active tier, each offering that
tier's two briefs (plus "neither — describe what you want" implicitly via
Other). Selected briefs get built; a tier can also be dropped here ("skip
Rethink for this surface").

**Open ledger-first.** When `wireframes/_library/decisions.md` has settled
verdicts touching this surface, present them before the pitches as **fixed
context** with one "reopen any of these?" affordance — a direction that
contradicts a settled verdict must say it is proposing to reopen it, not
silently route around it. Same law as the parent's interview: reopening is
cheap, re-asking is rude, silently dropping is dishonest.

## Unbuilt briefs are kept

A brief rejected at the directions round is recorded — in the spec's Rejected
Directions table as `rejected at: brief`, and appended to the ledger — with
lighter evidence weight than one rejected after being seen in the gallery
(`rejected at: gallery`). The distinction matters later: "we never built it"
and "we built it and it lost" justify different amounts of re-litigation when
someone proposes the same idea next quarter.

## Completeness scope per variant

Every built variant carries the **populated state with longest-case data** and
the **empty state** — empty is where redesigns quietly die, and a shared axis
makes it nearly free. Loading/error states and responsive behaviour are out of
scope by default and recorded as such in the spec, except one narrow-viewport
spot-check on the winner. The directions round includes one question offering
to pull any of these into scope.
