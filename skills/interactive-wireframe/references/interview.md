# Interview playbook — UI dimensions, previews, contradictions

Read before Phase 4. The wireframe is the instrument; this is how you play it.

## Round structure

- **≤4 questions per `AskUserQuestion` round.** More than that and answers get
  careless — and careless answers are worse than missing ones, because they look
  decided.
- **Rebuild between rounds.** Later questions are then asked against something
  real, and the user sees their previous answer already applied. This is the
  single highest-value habit in the loop: round 3 asked against round 2's
  wireframe gets better answers than all eight rounds asked upfront.
- **Ask the structural question before the aesthetic one.** Placement and
  ownership constrain treatment; the reverse wastes a round.
- **Prefer a control over a question.** If the answer is "it depends," that is
  not an answer to extract — it is an axis to add. Add it, and ask what should
  happen at each end.

## ASCII previews

Every option carries a preview. The bar: **a preview should let the user answer
without reading the label.** They cost little and they routinely change the
answer, because a description of a layout and the layout itself are different
objects.

Good — concrete, differences visible at a glance:

```
A · inline actions              B · overflow menu
┌──────────────────────────┐    ┌──────────────────────────┐
│ Order #1042   [Edit][··] │    │ Order #1042          [⋯] │
│ Fulfilled · 3 items      │    │ Fulfilled · 3 items      │
└──────────────────────────┘    └──────────────────────────┘
2 clicks to edit                1 control, edit is 2 clicks
always visible                  discoverable only on open
```

Bad — restates the label, shows nothing:

```
Option A: put the actions inline
```

Rules of thumb: use the **real strings** from grounding; keep all options the
same width so differences are structural not incidental; and put the *cost* of
each option in the preview, not just its shape.

## UI dimensions to cover

These complement the generic product dimensions in `spec-elicitation`. They are
the ones a wireframe is uniquely good at settling.

| Dimension | The question the wireframe makes answerable |
|---|---|
| **Layout ownership** | Who owns this region — the page, the layout, the shell? Decides whether the change is local or architectural |
| **Persistence & scroll** | What stays pinned, what leaves, what comes back and when |
| **Disclosure** | Expanded by default? Remembered across visits? Auto-collapse? |
| **Action placement** | Which single action is primary, where does it live, what happens to it when the container collapses |
| **Duplication** | Is anything now shown twice (a title in the header *and* the body)? |
| **Responsive degradation order** | What drops first, second, third — and where the dropped thing goes |
| **Permission & role variance** | Per role: what is hidden, what is disabled, what is read-only-but-visible |
| **Empty / one / many / overflow** | Zero-state copy, single-item layout, the long list, the too-long string |
| **In-flight & failure** | Pending treatment, optimistic or not, error placement, retry affordance |
| **Motion & reduced motion** | What animates, and that every state stays reachable without animation |
| **Markup & a11y constraints** | Nesting legality, focus order, what a keyboard user reaches |
| **Density & theme** | Compact vs comfortable; light vs dark if both ship |

You will not cover all twelve. Cover the ones this surface actually has, and say
which you skipped — an unasked dimension recorded as an open question is honest;
an unasked dimension silently assumed is a defect.

## Hunt contradictions — do not reconcile silently

Answers that are each individually sensible often cannot coexist. When you spot
it, **stop and surface it**. Silently picking one is the worst option: the user
believes both were honoured, and the spec encodes a decision nobody made.

Four shapes this takes, with the generic form:

| Shape | Example | Why it cannot hold |
|---|---|---|
| **Architecturally impossible** | "This bar is owned by the page" + "it is welded to the global header" | Page content cannot be a sibling of shell chrome without a slot mechanism — forces a real architectural decision |
| **Semantically empty** | "The steps come from customer-configured states" + "clicking a step opens that step's tab" | Configured states have no tab to open — the interaction has no target |
| **Duplicated** | "The title pins in the header" + "the H1 stays in the body" | The same string appears twice, 40px apart |
| **Recreated one level down** | "The breadcrumb ends in the item name" + "the header strip starts with it" | The collision you just moved has reappeared in the adjacent band |

How to surface one, in order:

1. **Name both answers** and quote them back.
2. **Say precisely what breaks** — not "these conflict" but "the title would
   render twice, 40px apart, in the same viewport."
3. **Show it if you can.** Build the contradictory state and screenshot it. A
   contradiction you can see is resolved in one round.
4. **Offer the resolutions as options**, including the "keep both, accept the
   cost" one — sometimes that genuinely is the answer.

Re-scan for contradictions after every round, against *all* prior answers, not
just the last one. Most of these only become visible on the third or fourth
round, when two distant decisions finally meet.

## Offer variants instead of arguing

When a disagreement is aesthetic, do not defend a choice — ship both as a
`variant` axis and put them side by side with `WF.compare()`. This converts an
argument into an observation, and it regularly ends with the user picking the
option neither of you was defending. It also produces something for the spec:
"we looked at four, here is why C won."

## When to stop

Stop when every axis has a decided value, every contradiction is resolved or
recorded, and the remaining unknowns are genuinely unknowable without building.
Then say what is **left open** rather than padding the spec to look complete —
an honest open question is cheap; a fabricated decision is expensive.

## Composing with `spec-elicitation`

Both directions work, and neither skill requires the other.

- **Mid-elicitation → wireframe.** When a `spec-elicitation` interview reaches a
  question that is really about layout, run this skill on that surface, then
  return with the locked layout decisions as answers. Carry over: the decision
  list, the wireframe URL, and any contradictions found.
- **Wireframe → elicitation.** When the wireframe settles the UI but the feature
  still needs the non-UI dimensions (data model, permissions enforcement,
  migration, rollout), hand the decision list to `spec-elicitation` and let it
  cover those rather than duplicating them here.

Either way the decision table is the interchange format: one row per decision,
each with an id, the choice, and whether the wireframe validated it visually.
