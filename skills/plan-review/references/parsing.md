# Phase 0 — Parse & Decompose

Goal: turn the prose artifact into a structured `artifact-map.md` that every later phase hangs on. You
do this yourself in the main session — the artifact is small, and carrying its structure in your own
context keeps grounding and review honest. A vague decomposition produces a vague review.

## Step 1 — Resolve the type (if `--type auto`)

Classify the artifact so the lenses tune correctly. Signal, strongest first:

- **Frontmatter** `type:` field — `plan`, `spec`, `issue`, `bug`, `feature`, `design` map directly.
- **Filename / path** — `plans/…`, `*-plan.md`, `spec`, `rfc`, `design-doc` → plan/spec;
  `issues/…`, `bug`, `ticket`, `BUG-`, `ISSUE-` → issue.
- **Structure** — phased task lists, "Implementation", "Steps", "Milestones" → **plan**. "Acceptance
  criteria", "Requirements", "Non-goals", "API" → **spec**. "Steps to reproduce", "Expected vs
  actual", "Severity", a single defect narrative → **issue**.

Record the resolved type and what you keyed off. When genuinely mixed (a plan that embeds a spec),
pick the dominant frame and note the secondary one — it widens the lenses, it doesn't break them.

## Step 2 — Decompose into the five buckets

Extract these from the artifact. Quote verbatim (with a line/section pointer back into the artifact)
so later phases and the final report can cite the exact words.

| Bucket | What it is | Why it matters downstream |
| ------ | ---------- | ------------------------- |
| **Tasks** | The concrete work the artifact proposes — steps, changes, deliverables. | Phase 1 grounds each one; Phase 2 checks sequencing, scope, and missing steps. |
| **Claims** | Statements the artifact asserts *about the codebase* — "the API returns X", "auth lives in `mw.ts`", "there's no caching today". | Phase 1 verifies each against real code; contradicted claims are the highest-value findings (errors). |
| **Assumptions** | Things taken for granted but not stated as fact — implied preconditions, "obviously we'll…", unstated dependencies, environment expectations. | Phase 2 (risk/feasibility) tests whether they hold; unheld assumptions are gaps. |
| **Acceptance criteria** | How the artifact says we'll know it's done — explicit criteria, "definition of done", or *the absence of any*. | Phase 2 (clarity) judges testability; missing/untestable criteria is a near-universal gap. |
| **Referenced components** | Every file, module, function, route, table, env var, package, or UI element the artifact names **or implies**. | The anchor list Phase 1 grounds. "Implied" matters: "add a settings toggle" implies a settings page + a store + persistence even if none are named. |

## Step 3 — Note what's conspicuously absent

While decomposing, jot the standard things a plan/issue of this type usually addresses but this one
doesn't — they become Phase 2's starting checklist, not findings yet:

- Plan/spec: tests, rollback/revert, data migration, error & empty states, observability/logging,
  security/authz, performance budget, backward compatibility, feature-flagging, docs, sequencing &
  dependencies between steps.
- Issue/bug: steps to reproduce, expected vs actual, environment/version, scope/blast radius,
  severity, suspected root cause, acceptance criteria for the fix.

Don't editorialize here — just mark presence/absence. Phase 2 decides if an absence is a real gap.

## Output — `artifact-map.md`

Write to `{ANALYSIS_DIR}/artifact-map.md`:

```markdown
# Artifact Map — {artifact filename}

- **Resolved type:** {plan | spec | issue}  (keyed off: {signal})
- **Title / intent (1 line):** {…}
- **Slug:** {ARTIFACT_SLUG}

## Tasks
- T1 — {task}  · _artifact:_ "{quote}" (§{section})
- …

## Claims about the codebase  (Phase 1 will verify each)
- C1 — {claim}  · _artifact:_ "{quote}"  · checkable: yes/no
- …

## Assumptions
- A1 — {assumption}  · explicit? no  · _basis:_ "{quote or 'implied by Tx'}"
- …

## Acceptance criteria
- {criterion, or "NONE STATED"}  · testable? yes/no

## Referenced components  (Phase 1 anchors)
| Anchor | Named or implied | First mention |
|--------|------------------|---------------|
| `mw.ts` auth middleware | named | "{quote}" |
| settings persistence store | implied by T3 | "{quote}" |

## Conspicuously absent (checklist for Phase 2 — not yet findings)
- [ ] rollback plan
- [ ] tests / acceptance criteria
- …
```

Keep it tight and faithful. If the artifact is three paragraphs, the map is short — that's correct.
