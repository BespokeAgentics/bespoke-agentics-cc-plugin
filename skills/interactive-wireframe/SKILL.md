---
name: interactive-wireframe
description: "Build a live, code-grounded HTML wireframe of a UI change, use it as the interview instrument, and emit a spec. Use this whenever someone says 'wireframe this', 'mock this up', 'sketch this screen', 'make a prototype/mockup of X', 'help me think through this UI/layout/header', 'show me what this would look like', 'try a few variants of this', or is going back and forth with themselves about a layout, sticky/scroll behaviour, what each role should see, where a control belongs, or how a screen should reorganise — even when they never say the word 'wireframe'. It detects the stack and lifts real design tokens, typography, enums/labels and roles from actual source (never inventing values), emits ONE self-contained HTML file (inline CSS + JS, no build step) carrying a control overlay generated from the axes that surface actually varies on — role switcher, entity states, permission toggles, thresholds, layout variants, zone guides, live state readout — serves it over local HTTP so it can be driven and measured in a browser, interviews in AskUserQuestion rounds with concrete ASCII previews while rebuilding the wireframe between rounds, verifies geometry/contrast/markup/behaviour with in-page assertions instead of eyeballing, and writes a spec grounded in real file paths. Prefer this over writing production UI code when the design is not settled, and over prose or ASCII mockups whenever the decision depends on real widths, real labels, real contrast, or real behaviour. Works on any stack with a UI. Not for auditing an existing interface (use a UX audit) and not for shipping the final component."
---

# Interactive Wireframe

Turn a UI argument into something you can click.

The premise: **people are much better at critiquing something concrete than at
answering a hypothetical.** "Should the header stay pinned while scrolling?" gets
a shrug. The same question asked while looking at a real header, with a real
scroll threshold on a slider, gets a decision in ten seconds — and often a
different decision than the one the prose was heading toward.

Two properties do the work, and neither is optional:

1. **Grounded in real code.** Real tokens, real labels, real enums, real roles,
   cited to real paths. This is what makes the wireframe *predictive* rather than
   merely illustrative — collisions, widths and contrast failures only appear
   with real values. Invented values produce a confident-looking picture of a
   product that does not exist.
2. **Interactive, not a picture.** A control overlay turns the mockup into a
   state explorer. Every control replaces a question you would otherwise ask in
   prose.

It ends with a spec, not a pretty file. The wireframe is evidence; the spec is
the artifact.

## When to use

Any UI change where the shape is genuinely undecided: reorganising a screen,
moving something into or out of chrome, sticky/scroll behaviour, disclosure,
where an action belongs, what each role sees, how a dense row survives a narrow
viewport.

**Skip it** when the design is already settled (just build it), when the change
is cosmetic (a colour, a copy edit), or when you are evaluating an interface that
already exists — that is a UX audit, not a wireframe.

## The loop

```
     ground in real code
             ↓
   build ──→ serve ──→ measure
     ↑                    ↓
     └── interview round ←┘        rebuild between rounds
             ↓
          emit spec
```

Phases 2–5 repeat. **Rebuilding between rounds is the highest-value habit here**
— round 4 asked against round 3's wireframe gets better answers than all rounds
asked upfront.

Calibrate to the change: a single component might be one wireframe and two
rounds; a screen restructure might be `v1` → `v2` and eight. Do not inflate a
small question into a ceremony.

## Phase 0 — Scope the surface

Establish exactly which surface, and what feels wrong about it today. One short
exchange, not an interview. If the target is ambiguous ("the dashboard" — which
one?), ask before grounding; grounding the wrong screen wastes the expensive
phase.

Pick a slug (`feature-detail-header`, `checkout-summary`) — it names the
wireframe directory and the spec.

## Phase 1 — Ground in real code

**Read `references/grounding.md`.** Detect the stack, then extract from source:
design tokens, typography, the real enums/labels the surface displays,
roles/personas/permission flags, the existing layout components the change
touches, behavioural constants, and data extremes.

Write `wireframes/<slug>/grounding.md` — the audit trail every later value cites.

Never invent a value. A missing token is a question; an invented one is a lie
that looks authoritative and gets copied into production. If the project has no
design system, say so and derive from the running app's computed styles, labelled
as derived.

## Phase 2 — Build the wireframe

Copy the scaffold and edit its four marked regions:

```sh
mkdir -p wireframes/<slug>
cp "$SKILL_DIR/assets/wireframe-scaffold.html" wireframes/<slug>/v1.html
```

The scaffold is self-contained by contract — inline CSS, inline JS, no build
step, opens by double-click. It already provides the control-overlay engine, URL
state, zone guides, the variant-comparison sheet, and the `__wf` verification
kit. You supply: tokens, surface styles, surface markup, and the axes.

- **`references/control-overlay.md`** — how to derive the axes this surface
  actually varies on, the axis types, and the variant-CSS rule.
- **`references/layout-patterns.md`** — read when the surface involves
  sticky/scroll behaviour, disclosure, or a clickable row that also carries
  actions. Ten defects with structural fixes, each found by building a wireframe
  rather than reasoning about one.

Render the surface at fidelity high enough to judge layout: real labels, real
longest-case strings, real affordances. Fidelity below that produces confident
answers to the wrong question.

## Phase 3 — Serve it

```sh
"$SKILL_DIR/scripts/serve-wireframe.sh" start wireframes/<slug>
```

Prints the URL. Serving over HTTP is **required** for browser automation —
`file:///…` gets rewritten to `https://file:///…` and fails. Responses are sent
`no-store`, so a rebuild is always what you measure.

The script starts at **8791 and deliberately never probes 8787** (`wrangler dev`'s
default, and a frequent collision), falls forward to 8799, names the process
holding any busy port, and reuses a server already running for that directory.
`--port N` forces one; `status` / `stop` do what they say.

If `python3` is missing it says so and stops rather than reporting a URL that
serves nothing.

## Phase 4 — Interview in rounds

**Read `references/interview.md`.**

- `AskUserQuestion`, **≤4 questions per round**, every option carrying a concrete
  ASCII preview built from real labels.
- **Rebuild between rounds** (`v1.html` → `v2.html` when the structure changes
  materially; edit in place for refinements).
- **Hunt contradictions and surface them.** Answers that are individually
  sensible often cannot coexist — one is architecturally impossible, one renders
  the same string twice, one recreates the collision you just moved. Say what
  breaks, show it if you can, and offer the resolutions. Silently reconciling is
  the worst outcome: the user believes both were honoured.
- **Offer variants instead of arguing.** When a disagreement is aesthetic, ship
  both as a `variant` axis and put them side by side with `WF.compare()`.

## Phase 5 — Verify, don't eyeball

**Read `references/browser-verification.md`.**

Drive the served page with browser automation and run the in-page assertions:
geometry contiguity, computed contrast ratios, markup validity, off-screen
focusables, and scripted behavioural sequences. Numbers belong in a spec;
impressions do not.

**Start every session with `__wf.env()`.** In a backgrounded tab, scroll events,
`requestAnimationFrame`, CSS transitions and `.focus()` all silently no-op — so a
behavioural "failure" is a measurement artifact until proven otherwise. The
playbook lists each failure mode and its workaround.

If browser automation is unavailable, serve the wireframe, hand the user the URL,
and interview against what *they* see — then label every unmeasured claim
**"not verified"** in the spec. A false green retires a test nobody ran.

## Phase 6 — Emit the spec

**Read `references/spec-template.md`.** Decisions (marking which the wireframe
validated visually), the structural contract with its measurements, architecture
with real paths, behaviour, states, verification results, risks, open questions,
out of scope, testing.

Resolve the path in this order: the project **wiki** if one exists (follow its
schema and log conventions) → **`./plans/<slug>.md`** → ask once and record the
answer in the project's `CLAUDE.md`.

Link the wireframe from the spec by relative path.

## Artifacts

```
<repo>/
├─ wireframes/<slug>/
│  ├─ grounding.md        every value, with its source path
│  ├─ v1.html             self-contained; opens with no build step
│  ├─ v2.html             later rounds, when structure changes materially
│  └─ .serve.json/.log    runtime state — add to .gitignore
└─ plans/<slug>.md        the spec (or the wiki, if the project has one)
```

Wireframes are **committed** by default so the spec's links resolve for anyone
who reads it later. Add `wireframes/**/.serve.*` to `.gitignore`. If the user
would rather not track them, `.wireframes/` gitignored works identically — say
which you chose.

## Composing with `spec-elicitation`

Standalone, or either direction — neither skill requires the other.

- **Mid-elicitation → wireframe.** When a `spec-elicitation` interview hits a
  question that is really about layout, run this on that surface and return with
  the locked layout decisions as answers.
- **Wireframe → elicitation.** When the wireframe has settled the UI but the
  feature still needs data model, permissions enforcement, migration and rollout,
  hand the decision table over rather than duplicating those dimensions here.

The decision table is the interchange format: one row per decision, each with an
id, the choice, and whether the wireframe validated it.

## Reference files

| File | Read when |
|---|---|
| `references/grounding.md` | Phase 1 — what to extract, where it lives per ecosystem, the no-design-system path |
| `references/control-overlay.md` | Phase 2 — deriving axes, axis types, variant-CSS scoping, comparison sheet |
| `references/layout-patterns.md` | Phase 2 — sticky stacks, scroll anchoring, nested buttons, focus guards, and six more |
| `references/interview.md` | Phase 4 — round structure, ASCII previews, UI dimensions, contradiction hunting |
| `references/browser-verification.md` | Phase 5 — hidden-tab checklist, the four assertion families |
| `references/spec-template.md` | Phase 6 — the output shape and where it goes |
| `assets/wireframe-scaffold.html` | Phase 2 — copy this; four marked REPLACE regions |
| `scripts/serve-wireframe.sh` | Phase 3 — `start` / `status` / `stop` / `url` |
