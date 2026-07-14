# Phase 3 — Highlight Selection Interview (the gate)

The user recorded a long demo; the reel is a *point of view* on it — which moments tell the story,
in what order, how long, in whose voice. That's the user's call, not the model's. First synthesize
a concrete proposal, then confirm it with **AskUserQuestion**. Never render before this gate.

## Step A — Synthesize `{ANALYSIS_DIR}/candidate-highlights.md`

From `moment-catalog.md` (salience) + `feature-source-map.md` (grounding), draft a ranked shortlist.
If `--duration` was given, pick enough top-salience moments to roughly fill it (assume ~8–20s per
moment); otherwise propose a natural set (~5–8 moments) and let the interview set the length.

```markdown
# Candidate Highlights — proposed cut

Proposed order (est. total ≈ {sum}s):
1. [12–27] **Dashboard metrics** — salience 5 — grounded: `Dashboard.tsx:44`, one query.
   Beat: "The dashboard opens with every KPI already populated — one API call, no spinner."
2. [48–61] **Global search** — salience 4 — grounded: `SearchBar.tsx:20`.
   Beat: "Search is instant and fuzzy, matching across records as you type."
3. …

Also-rans (available if you want a longer cut): [list]
Excluded (low salience: login, dead air, menu-hunting): [list]
```

Each candidate carries: window (in/out seconds), feature, salience, grounding ref, and a proposed
one-line narration beat.

## Step B — Print the digest (text, not a question)

```
Here's the demo as I read it and the cut I'd propose:
  • Demo length: {duration}s · {M} moments · {F} features (grounded {N}/{F})
  • Proposed reel (~{est}s): <numbered one-liners>
  • Left out: <low-salience list>
```

If there was no narration (silent source) or grounding was weak, say so here.

## Step C — The interview (AskUserQuestion)

Use **AskUserQuestion**. Max 4 questions per call; multiple calls are fine. Seed every option from
what the analysis actually found; offer your best inference first (mark "(Recommended)" only when
confidence justifies it). "Other" is always available — the user knows the story better than the
frames do.

**Q1 — Which moments make the cut?** (multiSelect) Options = the candidates + notable also-rans,
each labelled with its feature + window. Pre-recommend the proposed set. Unselected → excluded.

**Q2 — Target length / pacing.** (single) Only if `--duration` wasn't passed. Options e.g.
*Tight (~30s, punchy)* · *Standard (~60s)* · *Extended (~90s+, thorough)* · *Match my selection*.
This tunes how aggressively to trim windows and how terse the beats are.

**Q3 — Voice & tone.** (single) Tone: *Crisp product-marketing* · *Neutral explainer* ·
*Technical / developer-facing* · *Energetic launch trailer*. If `--voice` wasn't set and TTS is on,
you may also confirm the voice here (offer the stock default + "use a specific ElevenLabs voice_id").

**Q4 — Audio & captions.** (single or a small batch)
- Original audio under the voiceover: *Duck it (recommended)* · *Keep it full* · *Mute it*.
- Subtitles: *Burn them in (recommended)* · *SRT sidecar only, no burn*.
(Respect `--audio` / `--no-subs` if already passed — skip the redundant question.)

If order matters and Q1's selection is ambiguous, ask one short ordering question (or state you'll
keep demo chronological order unless told otherwise — usually the right default for a walkthrough).

## Step D — Persist `{ANALYSIS_DIR}/interview-answers.md`

Record the contract Phase 4 builds from:

```markdown
## Confirmed cut (in final order)
1. seg1 — Dashboard metrics — [12–27] — grounded Dashboard.tsx:44
2. seg2 — Global search — [48–61] — grounded SearchBar.tsx:20
…
## Settings
- target length: ~60s
- tone: technical / developer-facing
- voice_id: <id or default>
- original audio: duck   · subtitles: burn
## Dropped / deferred
- login, settings tour (low salience)
```

Set `REEL_SLUG` now if it wasn't given (from the confirmed theme, e.g. `acme-demo-highlights`).

Report: `Phase 3 complete. {K} moments confirmed, target ~{sec}s, tone {tone}`.
