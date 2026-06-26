# Phase 1 — Codebase Grounding

Goal: check the artifact against reality. Locate the real source behind every anchor the artifact map
names or implies, and mark every checkable claim as verified, contradicted, partial, or unresolved.
This is where the best findings come from — a plan reads as complete until you discover the code has
more surface than it assumed.

Skip this entire phase if `--no-ground` is set; the review then runs on the document alone and Phase 4
flags every feasibility finding as unconfirmed.

## Step 1 — Build the anchor work-list

From `artifact-map.md`, collect the referenced components (named **and** implied) plus the subjects of
each checkable claim. Cluster them so each grounding agent gets a coherent slice — group by
subsystem/feature, not one agent per symbol. Aim for 2–5 clusters at `standard`, fewer at `quick`,
more at `deep`.

For each cluster you also want the agent to answer the **"what else?"** question — the gap-revealing
part. Examples:

- The plan changes an API/function → who else **calls** it? (callers that also need updating)
- The plan edits one of something → is there **more than one**? (a second middleware chain, a parallel
  route, a duplicated component)
- The plan adds a field/column → does it imply a **migration**, a validator, a serializer, an index?
- The plan touches a flow → what **states** does the real code have that the plan ignores (loading,
  empty, error, unauthorized, offline)?

> Optional accelerator: if Rig MCP tools are available (`rig_callers`, `rig_impact`, `rig_search`,
> `rig_node`), they answer "who calls this / what breaks if I change this" faster and more completely
> than text search. Use them to seed the agents' work-lists. They are an optimization, never a
> dependency — the `Explore` agents must still confirm with `file:line`.

## Step 2 — Launch parallel `Explore` agents

One agent per cluster, all in a single response (multiple Agent calls). `Explore` is the right tool —
it locates code across many files and naming conventions and returns excerpts, not whole dumps. Prompt
each one with this shape (substitute `{variables}`):

```
You are grounding one cluster of a plan/issue review against the repo at {PROJECT_DIR}.
This is READ-ONLY: locate and report, do not modify anything.

Artifact claims & components to ground (this cluster):
{paste the cluster's anchors + the verbatim claims about them from artifact-map.md}

For EACH anchor:
- Find the real definition. Report `path:line` and a 1-line description, or "NOT FOUND" if it
  genuinely doesn't exist (search synonyms, casings, and conventions before concluding NOT FOUND).
For EACH claim:
- Verdict: VERIFIED / CONTRADICTED / PARTIAL / UNRESOLVED, with the `file:line` evidence that
  decides it. Quote the deciding code. CONTRADICTED is the most valuable — surface it clearly.
Then answer "what did the plan likely MISS here?":
- Other callers/consumers of anything it changes (list `file:line`).
- Duplicates / second implementations of anything it edits.
- Implied-but-unnamed work: migrations, validators, indexes, states (loading/empty/error/authz),
  config, tests that already exist and would break.
Be precise and skeptical. Never invent a path. "I could not confirm X" is a valid, useful result.

Return:
- grounded: [{anchor, path_line, note}]
- not_found: [{anchor, searched_for}]
- claim_verdicts: [{claim, verdict, evidence_file_line, quote}]
- missed: [{what, evidence_file_line, why_it_matters}]
```

## Step 3 — Synthesize `grounding-map.md`

After **all** agents return, merge into `{ANALYSIS_DIR}/grounding-map.md`:

```markdown
# Grounding Map — {artifact filename}

## Anchors grounded
| Anchor | Source | Note |
|--------|--------|------|
| auth middleware | `api/middleware.ts:30` | Express chain, runs on /api/* |
| auth middleware (2nd) | `edge/auth.ts:12` | **separate** edge chain — plan didn't mention it |

## Claim verdicts
| Claim | Verdict | Evidence | Quote |
|-------|---------|----------|-------|
| "auth lives only in mw.ts" | 🔴 CONTRADICTED | `edge/auth.ts:12` | `export function authEdge(...)` |
| "no caching today" | ✅ VERIFIED | — | (no cache layer found) |

## Not found / unresolved
| Anchor | Searched | Implication |
|--------|----------|-------------|
| `auth.ts` (as named in plan) | auth*, middleware*, guard* | plan names a file that doesn't exist |

## What the plan likely missed  (feeds Phase 2 completeness/feasibility)
- Changing `getUser()` affects 4 callers: `a.ts:10`, `b.ts:88`, … — plan only edits `a.ts`.
- Adding `users.role` implies a migration (`migrations/` exists) — plan has no migration step.
- The reset flow has an error state in `Filter.tsx:54` the plan's fix ignores.
```

Hand this, plus `artifact-map.md` and the artifact text, to every Phase 2 reviewer. The `missed`
section and any CONTRADICTED claim are pre-seeded findings — Phase 2 ranks and writes them up.

If an agent fails or a cluster resolves nothing, record it as unresolved and continue — a partial
grounding map is still far better than none.
