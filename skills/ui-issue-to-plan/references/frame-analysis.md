# Phase 1 — UI + Narration Analysis

Read the screens and the narration together. Output two artifacts: a map of what the UI shows, and
a list of the candidate "asks" the narrator is making. This phase is purely descriptive — it reads
pixels and words; it does not touch the codebase (that's Phase 2) and invents nothing.

## Step 1 — Compute chunk boundaries

Read `{FRAMES_DIR}/manifest.json`. Let `total_frames` = number of (deduped) frame entries.

- If `total_frames <= 8`, use a single chunk (one analyst).
- Otherwise split into up to 5 contiguous chunks: `chunk_size = ceil(total_frames / 5)`.

Each chunk covers a frame index range `[start, end]` and the narration words whose timestamps fall
in that range's time span.

## Step 2 — Launch parallel `ui-frame-analyst` agents

Launch one Agent per chunk, all in a single response (parallel). Use the `ui-frame-analyst` agent
type. Pass each agent:

```
chunk_id:       {N}
frame_range:    {start}..{end}
frames_dir:     {FRAMES_DIR}
manifest_path:  {FRAMES_DIR}/manifest.json
transcript_path:{ANALYSIS_DIR}/transcript.json   (or transcript.txt, or "none")
output_path:    {ANALYSIS_DIR}/frame-analysis-chunk-{N}.md
```

The agent's full instructions live in its definition (`agents/ui-frame-analyst.md`). In short, for
each frame in its range it records: the screen/route, the visible UI components (type + on-screen
label + rough location + state), the component(s) the narrator is pointing at, the problem or desire
expressed (with a verbatim quote + timestamp), and the on-screen text anchors that will help
grounding (exact labels, headings, URLs, error strings).

Wait for ALL analysts to finish before Step 3.

## Step 3 — Synthesize

Launch a single synthesis agent that reads every `frame-analysis-chunk-*.md` plus the transcript and
produces two files.

### `{ANALYSIS_DIR}/observed-ui-map.md`

A deduplicated, chronological map of the UI:

- **Screens / views** — each distinct screen (by route, title, or layout), in the order it appeared,
  with the frame timestamps where it's visible.
- **Components per screen** — every meaningful UI element: type (button / dropdown / modal / table /
  form field / nav item / toast / chart / etc.), its exact on-screen label, rough location
  (header / sidebar / main / footer / row N), and any observed state (default / error / empty /
  loading / disabled / selected).
- **Grounding anchors** — for each component, the exact strings a code search could match: visible
  label text, aria-ish labels if shown, headings, route paths in the URL bar, error messages.
- **Pointer trail** — which components the narrator's cursor / words single out, with timestamps.

### `{ANALYSIS_DIR}/issue-summary.md`

The narrated intent, distilled into discrete **candidate asks**. Each ask:

- `id` — short slug (e.g. `ask-1-dropdown-reset`).
- `title` — one line.
- `kind` — your best guess: **fix** (something is broken) / **change** (works but should behave
  differently) / **create** (new UI that doesn't exist yet). Mark low-confidence guesses.
- `what the narrator said` — verbatim quote(s) + timestamp(s).
- `components involved` — references into `observed-ui-map.md`.
- `inferred desired outcome` — your reading of what "done" looks like (stated as a requirement).
- `open questions` — anything ambiguous that the Phase 3 interview must resolve; mark `blocking: true`
  when the plan can't proceed without an answer.

Keep asks distinct and minimal — if the narrator circles back to the same problem, it's one ask.

If transcription was skipped, build `issue-summary.md` from on-screen evidence alone (errors, broken
layout, repeated focus on one element) and mark every ask `narration: missing` so Phase 3 fills the gap.

Report: `Phase 1 complete. {N} screens, {N} components, {N} candidate asks ({N} blocking questions)`.
