# Workflow Profile

Deliverable profile for analyzing workflows and recommending automation opportunities. This is the default profile — ideal for consulting engagements where you're documenting a client's current process to identify AI/automation opportunities.

## Primary Deliverable
`{DOCS_DIR}/{PROJECT_SLUG}-workflow-analysis.md`

## Wave Structure

```
Wave 1 (parallel): Transcript Deep Analysis ∥ Automation Opportunity Mapping
    ↓
Wave 2 (sequential): Final Report Synthesis
```

## Intermediate Deliverables
- `{DOCS_DIR}/application-inventory.md`
- `{DOCS_DIR}/workflow-timeline.md`
- `{DOCS_DIR}/friction-catalog.md`
- `{DOCS_DIR}/transcript-deep-analysis.md`
- `{DOCS_DIR}/automation-opportunities.md`

## Final Deliverables
- `{DOCS_DIR}/{PROJECT_SLUG}-workflow-analysis.md` — Full report (primary)
- `{DOCS_DIR}/{PROJECT_SLUG}-workflow-summary.md` — Executive summary

---

## Wave 1 — 3 Parallel Agents

All read from Phase 1 synthesis outputs.

### Agent 1: Application & Workflow Synthesis

```
Agent: "Application inventory and workflow mapping"
Prompt: |
  Analyze the screen catalog and component library for {project-name}'s {label} to produce workflow documentation.

  Read:
  - {DOCS_DIR}/screen-catalog.md
  - {DOCS_DIR}/component-library.md
  - {DOCS_DIR}/system-architecture-map.md
  - {FRAMES_DIR}/transcript.txt (if available)

  Produce TWO documents:

  1. **{DOCS_DIR}/application-inventory.md** — Complete inventory of every application/tool:
     - Application name and type (email client, CRM, spreadsheet, browser, etc.)
     - First and last seen timestamps
     - Total estimated screen time
     - Primary actions performed
     - Data types handled
     - Integration points with other tools

  2. **{DOCS_DIR}/workflow-timeline.md** — Chronological workflow map:
     - Every step in sequence with timestamps
     - Application transitions
     - Data flow between applications
     - Decision points and branching logic
     - Repetitive patterns (same sequence repeated)
```

### Agent 2: Transcript Deep Analysis (if transcript available)

```
Agent: "Deep transcript analysis"
Prompt: |
  Deeply analyze the transcript from {project-name}'s {label} recording.

  Read:
  - {FRAMES_DIR}/transcript.txt
  - {DOCS_DIR}/screen-catalog.md (for context)

  Extract and document:

  1. **Explicit pain points**: Every frustration or challenge mentioned. Quote directly with timestamps.
  2. **Implicit needs**: Wishes, desires, workarounds. Look for "I wish...", "It would be nice if...", "The problem is...", "This takes forever..."
  3. **Workflow rationale**: Why things are done in this order — understanding the WHY is critical for automation.
  4. **Volume and frequency data**: How often tasks occur, how many items processed, peak times.
  5. **People and roles**: Other people mentioned, their roles, dependencies.
  6. **Tool opinions**: Preferences or frustrations with specific tools.

  Save to: {DOCS_DIR}/transcript-deep-analysis.md
```

### Agent 3: Friction Catalog & Automation Mapping

```
Agent: "Friction catalog and automation opportunity mapping"
Prompt: |
  Analyze {project-name}'s {label} workflow for friction points and automation opportunities.

  Read ALL:
  - {DOCS_DIR}/screen-catalog.md
  - {DOCS_DIR}/component-library.md
  - {DOCS_DIR}/system-architecture-map.md

  Produce TWO documents:

  1. **{DOCS_DIR}/friction-catalog.md** — All friction points and challenges:
     - Observed friction (excessive steps, manual data transfer, context switching)
     - Error states or failures observed
     - Time sinks (estimated time per occurrence and frequency)
     - Workarounds observed
     - Severity rating for each (Critical / High / Medium / Low)

  2. **{DOCS_DIR}/automation-opportunities.md** — AI automation opportunity map:
     For each friction point and workflow step, assess:
     - Automation feasibility (Full / Assisted / Human-in-the-loop / Not automatable)
     - Implementation approach (Claude API, Computer Use, MCP servers, Custom agents, Claude Code)
     - Integration requirements
     - Risk assessment and guardrails needed
     - Impact estimate (time saved per occurrence × frequency)

     Categorize into:
     - **Quick Wins** (days to implement, high frequency)
     - **Medium-Term** (weeks, requires integrations)
     - **Transformative** (months, end-to-end redesign)
```

Wait for all 3 agents to complete.

---

## Wave 2 — Final Report Synthesis

```
Agent: "Synthesize workflow analysis report"
Prompt: |
  Produce the final deliverables for {project-name}'s {label} workflow analysis.

  Read ALL upstream documents:
  - {DOCS_DIR}/application-inventory.md
  - {DOCS_DIR}/workflow-timeline.md
  - {DOCS_DIR}/friction-catalog.md
  - {DOCS_DIR}/transcript-deep-analysis.md (if available)
  - {DOCS_DIR}/automation-opportunities.md
  - {FRAMES_DIR}/transcript.txt (if available, for direct quotes)

  Produce TWO deliverables:

  ### Deliverable 1: Full Workflow Analysis Report
  Save to: {DOCS_DIR}/{PROJECT_SLUG}-workflow-analysis.md

  Structure:
  # {project-name} Workflow Analysis: {label}
  *Generated [current date]*

  ## Table of Contents
  ## 1. Executive Summary
  - Overview of workflow analyzed
  - Key findings (3-5 points)
  - Overall automation potential (High/Medium/Low)
  - Estimated total time savings

  ## 2. Applications & Tools Inventory
  - Structured table + detailed descriptions per application
  - Role in workflow, actions observed, integration points, time spent

  ## 3. Complete Workflow Map
  - Step-by-step sequence with timestamps
  - Decision points and branching
  - Data flow diagram (ASCII)
  - Manual transfer points
  - Repetitive patterns with frequency

  ## 4. Challenges & Pain Points
  ### 4.1 Explicitly Stated (with transcript quotes)
  ### 4.2 Observed Friction Points
  ### 4.3 Workflow Gaps
  Each with: time impact (minutes × frequency) and severity

  ## 5. Automation Recommendations
  ### 5.1 Quick Wins
  ### 5.2 Medium-Term Improvements
  ### 5.3 Transformative Changes
  Each with: problem solved (ref Section 4), how it works, implementation, impact, prerequisites, risks

  ## 6. Prioritized Implementation Roadmap
  Ordered by impact-to-effort ratio, with dependencies, phases, success metrics

  ## 7. Appendix
  Complete tables, full timeline, glossary, pipeline metadata

  ### Deliverable 2: Executive Summary
  Save to: {DOCS_DIR}/{PROJECT_SLUG}-workflow-summary.md
  1-2 page summary: who, what, key findings, top 5 recommendations, next steps
```

Wait for synthesis to complete. Verify both files exist.
