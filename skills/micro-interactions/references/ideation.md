# Ideation: a small motion vocabulary, then many ideas built from it

The failure mode of "give me micro-interactions" is a list of 30 unrelated effects:
a bounce here, a confetti there, a shimmer on every card. Each one is defensible; the
set has no grammar, so the app ends up noisy and inconsistent. This skill inverts it:
**choose 4–6 motions first, then express every idea as one or more of them.**

## Step 1: the motion vocabulary

Start from what ships. Every motion the app already has (found in discovery) is a
vocabulary entry with `status: "ships"`. Then add **new** motions only where a flow
needs a job that no shipped motion does. Five jobs cover almost every app:

| Job | Question it answers | Canonical motion (rename to fit the app) |
|---|---|---|
| **Notice** | "Something changed that I did not do" | **Latch**: the element takes the state hue, holds about 1 s, fades to its rest color over about 2.4 s. Color only, so it survives reduced motion. |
| **Readout** | "A number changed; which way?" | **Tick**: the new value rolls in from the direction of change (0.28 s, 0.32 em, a 2 px blur that clears), once. |
| **Resolve** | "Is it done? Did it work?" | **Settle**: the in-flight mark (a dashed ring) closes into a solid dot in the outcome hue (0.32 s ring + 0.26 s dot). |
| **Route** | "Where did my request go?" | **Handoff**: a small ghost travels from the control to the place that tracks the request (≈ 0.56 s), and that place's count ticks. |
| **Acknowledge** | "Did my press do anything?" | **Echo**: the control answers in words where it was pressed ("Asked 2 agents", "No changes", "Cleared 4 · Undo"), then becomes its lasting state. |

Rules for the vocabulary:

- **Name motions in the app's own idiom.** If the design system already calls its
  change highlight a "flash", the motion is Flash, not Latch.
- **Pick a signature.** One new motion should be the one that expresses *this* app's
  character, derived from a rule it already has. Example: a board whose design rule is
  "dashed means not final" gets Settle (the dashed rule, made to move) as its
  signature. Say why in `page.json → vocab_p`.
- **4–6 motions total.** Fewer than 4 cannot cover the flows; more than 6 is no longer
  a vocabulary.
- Each motion gets a one-line `spec` (duration, distance, what survives reduced
  motion) so an engineer can build it from the card alone.

## Step 2: ideas per flow

Walk each flow from discovery and ask, at every state change:

1. **Who caused it?** Not the person → it needs **Notice** (and, where it matters,
   *who* did it: "moved by sandbox-seed").
2. **Is there a number?** → **Tick** it from the direction of change.
3. **Is there a wait?** → an in-flight mark that **Settles** into the outcome, with
   elapsed time in tabular figures while waiting.
4. **Does the outcome land somewhere else?** → **Handoff** to that place.
5. **Did the person press something whose effect is invisible or delayed?** → **Echo**.
6. **Can it be undone?** A destructive action with no undo is a behavior gap, not
   a motion. Propose it, and flag it as a behavior change.
7. **Coming back after being away** (tab hidden, offline, a long scroll)? → one line
   that says what happened meanwhile, then gets out of the way.

Aim for **5–8 ideas per flow, 25–40 total.** Fewer is fine for a small app; never pad.
Each idea is one concrete change on one named surface, not a theme.

## Step 3: fill every field

Each idea in `data.js` needs all of:

| Field | Write |
|---|---|
| `id` | Flow letter + number: `A1`, `B3`. Letters follow flow order. |
| `title` | What the person will notice, as a sentence: "The command bar settles its result". |
| `why` | The current behavior and its cost, specifically: "Running swaps to Fast · just now with no transition, so the result is easy to miss." |
| `trigger` | The exact event: "A run settles", "Clear finished", "SSE reconnects after an offline spell". |
| `moves` | What moves, how far, how long, in the app's labels. |
| `reduced` | What remains under `prefers-reduced-motion`. Never "nothing": color, words and state changes stay. |
| `where` | Function name(s) + file from discovery's code anchors. |
| `prims` | Motion ids from the vocabulary. |
| `impact` | 3: fixes a missed outcome, lost work or a false belief. 2: makes a state clearer. 1: polish. |
| `effort` | 1: under half a day (CSS + a class toggle). 2: about a day (new JS state, a view transition). 3: several days (new data, new route, new component). |
| `first` | `true` for the first batch (Step 4). |

**Flag behavior changes.** If an idea changes what the app *does* (an Undo, a filter,
a new notice, a new route), say so in `moves` and list it in the summary to the user.
Those need a product decision, not just motion review.

## Step 4: the first batch

Choose 6–10 ideas, mostly high impact and low effort, then **order them so shared
work comes first**: the idea that builds a reusable motion (one CSS rule, one helper)
goes before the ideas that reuse it. Write the order and a one-line reason for each
into `MI.firstOrder`.

## Step 5: the walkthrough

Pick **one** realistic journey through the app that fires the first-batch ideas in a
natural order: 4–7 steps. Each step names its idea ids and says, in one or two
sentences, what the person sees and why. The walkthrough is the page's argument; the
catalogue is its evidence.

## Guardrails (always on the page)

Write a **Never** list and an **Always** list from the app's own rules plus these
defaults (drop any the app's design authority overrides):

- Never loop. A settled page runs zero animations.
- Never count a number up from zero; it fakes work.
- Never shake, bounce or wobble on an error. Show the problem and the recovery.
- Never celebrate a routine click. Keep celebration for rare, consequential moments.
- Never animate the first render, a filter, or a change the person just made
  themselves (they already see the result).
- Always: reduced motion keeps the meaning (color, words, dashed → solid stay).
- Always: exits faster than entrances.
- Always: one easing curve across the app.
- Always: words with the motion; what an Echo says also reaches `role="status"`.
- Always: a state color means a state; brand colors never do.
