# Phase 1 — Moment Analysis

Turn the raw frame timeline + transcript into a **moment catalog**: an ordered list of the distinct
things that happen in the demo, each with a timestamp window, what's shown, what's said, the feature
it demonstrates, and how highlight-worthy it is. This is the raw material selection draws from.

## Step 1 — Chunk the timeline

Read `{FRAMES_DIR}/manifest.json`. Split the frames into contiguous chunks of ~20–30 frames each
(so each analyst agent has a bounded, overlapping-free slice). Compute each chunk's start/end
`timestamp_seconds` from the manifest. For a very short demo (< ~30 frames) a single chunk is fine.

## Step 2 — Launch parallel frame-analyst agents

One agent per chunk, all launched in a single response. Each agent MUST use the Read tool to look at
the actual frame PNGs — not guess from filenames.

```
Agent type: general-purpose  (or ui-frame-analyst if you prefer the bundled analyst)
Prompt: |
  You are analyzing a slice of an application-demo screen recording to find the moments worth
  putting in a highlight reel.

  Frames: {FRAMES_DIR}/frame_{first}.png … frame_{last}.png  (read each with the Read tool).
  Manifest: {FRAMES_DIR}/manifest.json — gives each frame's timestamp_seconds.
  Transcript: {ANALYSIS_DIR}/transcript.json — a `words` array with per-word start times. Use it to
  find what the presenter SAID during this chunk's time window (align by timestamp).

  For this chunk, produce an ordered list of distinct MOMENTS. Merge adjacent frames that show the
  same thing into one moment. For each moment give:
    - window: start–end in seconds (from the manifest)
    - screen: what app screen / view is shown
    - action: what happens (a click, a navigation, data loading, a result appearing, an error, etc.)
    - said: the presenter's words during this window (verbatim-ish from the transcript), or "(silent)"
    - feature: the product feature being demonstrated, named plainly (e.g. "global search",
      "bulk export", "role-based permissions")
    - salience: 1–5 — how highlight-worthy. Score HIGH for: the feature's payoff/result moment, a
      "wow" interaction, something the presenter emphasizes verbally, a clear before→after. Score LOW
      for: loading spinners, dead air, hunting for a menu, repeated identical states, setup/login.
    - onscreen_text: any exact button labels, headings, or messages visible (these become grounding anchors)

  Return as a markdown table plus, for each salience≥4 moment, one sentence on WHY it matters.
  Cite the frame indices you based each moment on.
```

Wait for all chunk agents to finish.

## Step 3 — Synthesize `{ANALYSIS_DIR}/moment-catalog.md`

Merge the chunk outputs into one continuous, de-duplicated, time-ordered catalog. Resolve overlaps
at chunk boundaries (same moment reported by two agents → keep one, widen the window). Structure:

```markdown
# Moment Catalog — {source} ({duration}s)

| # | Window (s) | Screen | Action | Feature | Said (abridged) | Salience | On-screen anchors |
|---|-----------|--------|--------|---------|-----------------|----------|-------------------|
| 1 | 0–12      | Login  | Auth + redirect to dashboard | authentication | "...log in..." | 2 | "Sign in", "Welcome back" |
| 2 | 12–27     | Dashboard | KPIs render from one API call | dashboard metrics | "...instantly, no spinner..." | 5 | "Monthly revenue", "Active users" |
| … |

## Highlight candidates (salience ≥ 4), in demo order
- **[12–27] Dashboard metrics** — the payoff moment; presenter stresses speed. Anchors: "Monthly revenue".
- …

## Distinct features demonstrated (for grounding)
- authentication · dashboard metrics · global search · bulk export · …
```

The **Distinct features** list feeds Phase 2 (grounding) — one grounding target per feature. The
**Highlight candidates** list feeds Phase 3 (selection).

Report: `Phase 1 complete. {M} moments catalogued, {K} high-salience candidates, {F} distinct features`.
