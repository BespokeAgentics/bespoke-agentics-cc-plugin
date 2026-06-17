---
name: "bespokeagentics:ui-issue-to-plan"
description: "Turn a narrated screen recording into a grounded implementation plan that captures BOTH what to fix AND how to improve the experience. Reads the frames to identify the UI components being referenced, transcribes the narration, maps the observed components to real source files in the CURRENT repo (file:line), surfaces a curated set of grounded improvement opportunities, runs an AskUserQuestion interview that frames intent (fix vs improve) and lets you opt into enhancements, then writes a plan to ./plans/ with separate Defect-fix and Enhancement sections. For .mp4/.mov/.webm/.gif screencasts of a bug, layout glitch, desired change, or how a flow should work better in the project open in this session."
argument-hint: "'<video-path>' [issue-label] [interval] [--mode fix|improve|both] [--out <dir>] [--no-ground] [--skip-dedup] [--skip-transcribe] [--force]"
allowed-tools: Skill(ui-issue-to-plan), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# UI Issue → Plan

Run the `ui-issue-to-plan` skill: read a narrated UI screencast, ground it in this
repo's source, interview the user to lock the intent, and write an implementation plan.

## Arguments

Parse from `$ARGUMENTS`:

```
'<video-path>' [issue-label] [interval] [--mode fix|improve|both] [--out <dir>] [--no-ground] [--skip-dedup] [--skip-transcribe] [--force]
```

- `<video-path>` (required) — local screencast (`.mp4`, `.mov`, `.webm`, `.gif`).
- `issue-label` (optional) — short name → output filename slug; else derived from the validated intent.
- `interval` (optional, default `2`) — seconds between extracted frames.
- `--mode fix|improve|both` (default `both`) — `fix` = defects only; `improve` = lean into
  enhancements; `both` = calibrated (a framing beat sets the altitude so quick bugs stay lean).
- `--out <dir>` (default `./plans`) — where the plan is written.
- `--no-ground` — skip codebase grounding (video + narration only).
- `--skip-dedup` / `--skip-transcribe` / `--force` — as in the skill.

## Process

Invoke the `ui-issue-to-plan` skill and forward `$ARGUMENTS`. The skill will:

1. **Preprocess** — extract frames, dedup, transcribe the narration (with word timestamps).
2. **Analyze** — parallel `ui-frame-analyst` agents read the frames + narration → an
   observed-UI map and an issue summary (candidate fixes **plus** the narrator's vision and
   observed opportunity signals).
3. **Ground** — parallel `Explore` agents map each observed component to real source
   `file:line` in the current repo (unless `--no-ground`).
4. **Opportunities** — unless `--mode fix`, synthesize a curated 3–5 grounded improvement
   proposals (`opportunities.md`).
5. **Interview** — AskUserQuestion batches: a framing/vision beat (fix vs improve), confirm each
   fix, confirm uncertain source locations, set priority, and opt into enhancements.
6. **Plan** — write `./plans/<slug>.md`: context, on-screen evidence (frame + quote),
   affected files (`file:line`), **separate Defect-fix and Enhancement sections**, a grouped
   task checklist, deferred opportunities, open questions, and verification. Wiki-ingested if a
   vault exists.

## Output

`{OUT_DIR}/<issue-slug>.md` (the implementation plan, fixes + enhancements), plus intermediate
artifacts under `ui-issue-analysis/` (observed-ui-map, issue-summary, component-source-map,
opportunities, interview-answers). Ends with a summary and an offer to start the P0 task — but
does not edit code until you say so.
