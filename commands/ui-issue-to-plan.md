---
name: "bespokeagentics:ui-issue-to-plan"
description: "Turn a narrated screen recording of a UI issue into a grounded implementation plan. Extracts and reads the frames to identify the UI components being referenced, transcribes the narration, maps the observed components to real source files in the CURRENT repo (file:line), runs an AskUserQuestion interview to pin down exactly what to fix/create/update, then writes an implementation plan to ./plans/. For .mp4/.mov/.webm/.gif screencasts of a bug, layout glitch, or desired UI change in the project open in this session."
argument-hint: "'<video-path>' [issue-label] [interval] [--out <dir>] [--no-ground] [--skip-dedup] [--skip-transcribe] [--force]"
allowed-tools: Skill(ui-issue-to-plan), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# UI Issue → Plan

Run the `ui-issue-to-plan` skill: read a narrated UI screencast, ground it in this
repo's source, interview the user to lock the intent, and write an implementation plan.

## Arguments

Parse from `$ARGUMENTS`:

```
'<video-path>' [issue-label] [interval] [--out <dir>] [--no-ground] [--skip-dedup] [--skip-transcribe] [--force]
```

- `<video-path>` (required) — local screencast (`.mp4`, `.mov`, `.webm`, `.gif`).
- `issue-label` (optional) — short name → output filename slug; else derived from the validated intent.
- `interval` (optional, default `2`) — seconds between extracted frames.
- `--out <dir>` (default `./plans`) — where the plan is written.
- `--no-ground` — skip codebase grounding (video + narration only).
- `--skip-dedup` / `--skip-transcribe` / `--force` — as in the skill.

## Process

Invoke the `ui-issue-to-plan` skill and forward `$ARGUMENTS`. The skill will:

1. **Preprocess** — extract frames, dedup, transcribe the narration (with word timestamps).
2. **Analyze** — parallel `ui-frame-analyst` agents read the frames + narration → an
   observed-UI map and a list of candidate asks (fix / change / create) with evidence.
3. **Ground** — parallel `Explore` agents map each observed component to real source
   `file:line` in the current repo (unless `--no-ground`).
4. **Interview** — AskUserQuestion batches confirm each ask, clarify the desired outcome,
   confirm uncertain source locations, and set priority — eliciting a clear vision of
   what to fix/create/update.
5. **Plan** — write `./plans/<slug>.md`: context, on-screen evidence (frame + quote),
   affected files (`file:line`), proposed changes, an ordered task checklist, open
   questions, and a verification section. Wiki-ingested if a vault exists.

## Output

`{OUT_DIR}/<issue-slug>.md` (the implementation plan), plus intermediate artifacts under
`ui-issue-analysis/` (observed-ui-map, issue-summary, component-source-map,
interview-answers). Ends with a summary and an offer to start the P0 task — but does not
edit code until you say so.
