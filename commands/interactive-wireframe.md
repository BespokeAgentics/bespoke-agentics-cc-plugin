---
name: "bespokeagentics:interactive-wireframe"
description: "Build a live, code-grounded HTML wireframe of a UI change and use it as the interview instrument, then emit a spec. Lifts real design tokens, typography, enums/labels and roles from THIS repo's source (never invents values), emits ONE self-contained HTML file (inline CSS + JS, no build step) carrying a control overlay generated from the axes the surface actually varies on — role switcher, entity states, permission toggles, thresholds, layout variants, zone guides — serves it over local HTTP so it can be driven and measured in a browser, interviews in AskUserQuestion rounds with ASCII previews while rebuilding between rounds, verifies geometry/contrast/markup/behaviour with in-page assertions instead of eyeballing, and writes a spec grounded in real file paths. For 'wireframe this', 'mock this up', 'help me think through this UI', 'try a few variants'. Works on any stack with a UI. Distinct from ux-audit (evaluates an existing interface) and data-ui-craft (fixes display craft): this one settles an UNDECIDED design before it is built."
argument-hint: "'<surface>' [--slug <name>] [--rounds N] [--port N] [--out <dir>] [--spec <path>] [--no-verify] [--no-serve]"
allowed-tools: Skill(interactive-wireframe), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep, Agent
---

# Interactive Wireframe

Run the `interactive-wireframe` skill: ground a UI change in this repo's real source, build a
self-contained interactive wireframe, interview against it, verify it in a browser, and write a
spec. **No production code is written** — the output is a wireframe plus a spec.

## Arguments

Parse from `$ARGUMENTS`:

```
'<surface>' [--slug <name>] [--rounds N] [--port N] [--out <dir>] [--spec <path>] [--no-verify] [--no-serve]
```

- `<surface>` (required) — the surface under discussion: a route, a component name, a page, or a
  description ("the feature detail header", "the checkout summary step"). Ambiguous targets are
  clarified before grounding starts.
- `--slug <name>` (default: derived from the surface) — names `wireframes/<slug>/` and the spec.
- `--rounds N` (default: as many as the change needs) — cap the interview. Use `--rounds 1` for a
  quick sketch; a screen restructure typically wants 4–8.
- `--port N` (default `8791`) — serve port. **8787 is never auto-probed** (`wrangler dev`'s default);
  pass `--port 8787` to force it. Falls forward to 8799 and names whatever holds a busy port.
- `--out <dir>` (default `./wireframes`) — where the wireframe HTML and grounding notes are written.
- `--spec <path>` (default: wiki plans dir if a vault exists, else `./plans/<slug>.md`).
- `--no-verify` — skip the browser-verification pass. Everything unmeasured is then labelled
  "not verified" in the spec rather than claimed.
- `--no-serve` — build the file only, don't start a server (browser automation will not work).

## Process

Invoke the `interactive-wireframe` skill and forward `$ARGUMENTS`. The skill will:

1. **Scope** — pin down exactly which surface, and what feels wrong about it today.
2. **Ground** — detect the stack and extract real design tokens, typography, enums/labels, roles and
   permission flags, the existing layout components the change touches, and behavioural constants —
   each cited to a path → `wireframes/<slug>/grounding.md`. Nothing is invented; a project with no
   design system gets values derived from computed styles, labelled as derived.
3. **Build** — emit `wireframes/<slug>/v1.html`: one self-contained file (inline CSS + JS, no build
   step) with real tokens in `:root` and a **control overlay generated from the axes this surface
   actually varies on**, plus zone guides, a live state readout, URL-encoded state, a variant
   comparison sheet, and the in-page verification kit.
4. **Serve** — local HTTP on 8791 (required: `file://` URLs fail under browser automation), reusing a
   live server for the same directory.
5. **Interview** — AskUserQuestion rounds of ≤4, every option carrying a concrete ASCII preview, with
   the wireframe **rebuilt between rounds** so later questions are asked against something real.
   Contradictions between answers are surfaced rather than silently reconciled; aesthetic
   disagreements become switchable variants shown side by side.
6. **Verify** — drive the served page and assert: band/region geometry contiguity, computed contrast
   ratios, markup validity (`button button`, dangling `aria-controls`, unnamed controls), off-screen
   focusables, and scripted behavioural sequences. Backgrounded-tab caveats are checked first — in a
   hidden tab scroll events, rAF, transitions and `.focus()` all silently no-op.
7. **Spec** — write the spec with decisions (marking which the wireframe validated visually), the
   structural contract with its measurements, architecture with real paths, behaviour, states,
   verification results, risks, open questions, out of scope, and testing. Wiki-ingested if a vault
   exists.

## Output

- `wireframes/<slug>/v1.html` (and `v2.html`… as rounds change the structure) — self-contained,
  committed by default so the spec's links resolve for anyone reading it later.
- `wireframes/<slug>/grounding.md` — every value with its source path.
- The spec at `--spec`, the wiki, or `./plans/<slug>.md`.

Ends with the wireframe URL, the decision count, what the verification pass measured, and anything
left open — then **offers** to start implementing. It does not write production code unprompted.
