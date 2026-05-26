# Phase 2 — Workflow documentation & automation recommendations

## Step 1 — Launch parallel analysis agents

Launch both in a single response (parallel).

### Transcript deep analysis (if transcript available)

```
Agent: "Deep transcript analysis for workflow insights"
Prompt: |
  Deeply analyze the transcript from {client-name}'s workflow recording.

  Read:
  - {FRAMES_DIR}/transcript.txt
  - {DOCS_DIR}/application-inventory.md

  Extract and document:

  1. **Explicit pain points** — every frustration, complaint, or challenge {client-name} mentions. Quote directly with timestamps.
  2. **Implicit needs** — wishes and unmet desires. Look for "I wish...", "It would be nice if...", "The problem is...", "This takes forever...", "I have to manually..."
  3. **Workflow rationale** — why {client-name} does things in this particular order. The WHY behind each step is critical for automation recommendations.
  4. **Volume and frequency data** — how often tasks occur, item counts, peak times.
  5. **People and roles** — other people mentioned, their roles, what they need from {client-name}'s workflow.
  6. **Tool opinions** — preferences and frustrations with specific tools.

  Save to: {DOCS_DIR}/transcript-deep-analysis.md
```

### Automation opportunity mapping

```
Agent: "Map automation opportunities to AI agent capabilities"
Prompt: |
  You are an AI automation strategist. Analyze {client-name}'s workflow to identify every opportunity for Claude/AI agent automation.

  Read:
  - {DOCS_DIR}/application-inventory.md
  - {DOCS_DIR}/workflow-timeline.md
  - {DOCS_DIR}/friction-catalog.md

  For each workflow step and friction point, assess:

  1. **Automation feasibility** — Full automation / Assisted automation / Human-in-the-loop / Not automatable.
  2. **Implementation approach** — Claude API for text processing/classification/drafting; computer use for GUI automation; MCP servers for tool integration; custom agents for multi-step workflows; Claude Code for developer workflows.
  3. **Integration requirements** — APIs, tools, access needed.
  4. **Risk assessment** — what could go wrong, guardrails needed.
  5. **Impact estimate** — time saved per occurrence × frequency = weekly/monthly impact.

  Categorize opportunities into:
  - **Quick Wins** (days to implement, high frequency tasks)
  - **Medium-Term** (weeks, requires integrations)
  - **Transformative** (months, end-to-end workflow redesign)

  Save to: {DOCS_DIR}/automation-opportunities.md
```

Wait for both to complete.

## Step 2 — Synthesize final report

```
Agent: "Synthesize comprehensive workflow analysis report"
Prompt: |
  You are producing the final client deliverable for {client-name}'s workflow analysis.

  Read ALL upstream documents:
  - {DOCS_DIR}/application-inventory.md
  - {DOCS_DIR}/workflow-timeline.md
  - {DOCS_DIR}/friction-catalog.md
  - {DOCS_DIR}/transcript-deep-analysis.md (if available)
  - {DOCS_DIR}/automation-opportunities.md
  - {FRAMES_DIR}/transcript.txt (if available, for direct quotes)

  Produce TWO deliverables — see `references/deliverable-template.md` for the full report structure and the executive summary template:
  - {DOCS_DIR}/{CLIENT_SLUG}-workflow-analysis.md — full report
  - {DOCS_DIR}/{CLIENT_SLUG}-workflow-summary.md — 1–2 page executive summary
```

Wait for synthesis to complete. Verify both deliverables exist.

Report: `Phase 2 complete. Full workflow analysis and executive summary generated`.
