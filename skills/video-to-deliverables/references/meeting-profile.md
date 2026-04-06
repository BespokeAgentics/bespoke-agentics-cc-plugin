# Meeting Profile

Deliverable profile for synthesizing meeting recordings into actionable summaries. Ideal for stand-ups, strategy sessions, client calls, or any meeting where you need structured notes, action items, and follow-up plans.

## Primary Deliverable
`{DOCS_DIR}/{PROJECT_SLUG}-meeting-summary.md`

## Wave Structure

```
Wave 1 (parallel): Topic Extractor ∥ Action Item Tracker
    ↓
Wave 2 (sequential): Meeting Summary Synthesis
```

## Final Deliverables
- `{DOCS_DIR}/{PROJECT_SLUG}-meeting-summary.md` — Structured meeting summary (primary)
- `{DOCS_DIR}/{PROJECT_SLUG}-action-items.md` — Action items with owners and deadlines
- `{DOCS_DIR}/{PROJECT_SLUG}-follow-up-agenda.md` — Suggested follow-up meeting agenda

---

## Wave 1 — 2 Parallel Agents

### Agent 1: Topic & Decision Extractor

```
Agent: "Extract meeting topics and decisions"
Prompt: |
  Analyze the recording for "{project-name}" ({label}) to extract topics, decisions, and key discussion points.

  Read:
  - {FRAMES_DIR}/transcript.txt (if available)
  - {DOCS_DIR}/screen-catalog.md
  - {DOCS_DIR}/component-library.md

  Document:
  1. **Topics discussed** — Each topic with start/end timestamps, key points, participants (if identifiable from transcript)
  2. **Decisions made** — Every decision with context, rationale, and who made it
  3. **Questions raised** — Both answered and unanswered, with context
  4. **Demos/presentations shown** — What was demonstrated on screen (from frame analysis), key takeaways
  5. **Disagreements or open debates** — Positions taken, resolution status

  Save to: {DOCS_DIR}/meeting-topics-{LABEL}.md
```

### Agent 2: Action Item & Commitment Tracker

```
Agent: "Track action items and commitments"
Prompt: |
  Extract every action item, commitment, and follow-up from the "{project-name}" ({label}) recording.

  Read:
  - {FRAMES_DIR}/transcript.txt (if available)
  - {DOCS_DIR}/screen-catalog.md

  For each action item:
  - What needs to be done (specific, actionable description)
  - Who is responsible (if mentioned)
  - Deadline or timeframe (if mentioned)
  - Context (why this came up)
  - Priority (inferred from discussion urgency)
  - Dependencies (blocked by other items?)

  Also capture:
  - Commitments made ("I'll have that by Friday", "We'll revisit next week")
  - Deferred items ("Let's table that for now", "We'll discuss offline")

  Save to: {DOCS_DIR}/action-items-raw-{LABEL}.md
```

Wait for both agents to complete.

---

## Wave 2 — Meeting Summary Synthesis

```
Agent: "Synthesize meeting summary"
Prompt: |
  Produce final meeting deliverables for "{project-name}" ({label}).

  Read ALL:
  - {DOCS_DIR}/meeting-topics-{LABEL}.md
  - {DOCS_DIR}/action-items-raw-{LABEL}.md
  - {FRAMES_DIR}/transcript.txt (if available)

  Produce THREE deliverables:

  ### 1. Meeting Summary
  Save to: {DOCS_DIR}/{PROJECT_SLUG}-meeting-summary.md

  # {project-name}: {label}
  *[date]*

  ## Key Takeaways (3-5 bullet points)
  ## Topics Discussed (chronological, with timestamps)
  ## Decisions Made
  ## Action Items (summary table: item | owner | deadline | status)
  ## Open Questions
  ## Parking Lot (deferred items)

  ### 2. Action Items
  Save to: {DOCS_DIR}/{PROJECT_SLUG}-action-items.md

  Structured, trackable format:
  - Grouped by owner (or "Unassigned")
  - Each with: description, deadline, context, priority, dependencies
  - Checklist format (- [ ] item) for easy tracking

  ### 3. Follow-Up Agenda
  Save to: {DOCS_DIR}/{PROJECT_SLUG}-follow-up-agenda.md

  Suggested agenda for the next meeting:
  - Open items from this meeting that need follow-up
  - Deferred/parking lot items
  - Decisions that need validation
  - Suggested time allocations
```

Wait for synthesis to complete.
