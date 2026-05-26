# Final deliverable templates

## Deliverable 1 — Full workflow analysis report

Save to: `{DOCS_DIR}/{CLIENT_SLUG}-workflow-analysis.md`

```markdown
# {client-name} Workflow Analysis: {workflow-label}
*Generated [current date]*

## Table of Contents

## 1. Executive Summary
- Overview of the workflow analyzed
- Key findings (3–5 bullet points)
- Overall automation potential (High/Medium/Low with justification)
- Estimated total time savings achievable

## 2. Applications & Tools Inventory
For EVERY application identified, document in a structured table AND detailed descriptions:
- Application name and type
- Role in the workflow
- How {client-name} uses it (specific actions observed)
- Integration points with other tools
- Estimated time spent
- Frame references (timestamps)

## 3. Complete Workflow Map
- Step-by-step sequence with timestamps
- Decision points and branching logic
- Data flow diagram (ASCII / text-based)
- Manual transfer points between systems
- Repetitive patterns with frequency estimates

## 4. Challenges & Pain Points

### 4.1 Explicitly Stated Challenges
- Direct quotes from {client-name} with timestamps
- Impact assessment for each

### 4.2 Observed Friction Points
- Context switching overhead
- Manual data transfer operations
- Repetitive manual tasks
- Error-prone steps
- Waiting / loading time

### 4.3 Workflow Gaps
- Missing integrations
- Information silos
- Lack of tracking / analytics
- No standardized process documentation

For each challenge: time impact (minutes per occurrence × frequency) and severity rating.

## 5. Automation & Agentic Enhancement Recommendations

### 5.1 Quick Wins (Implement within days)
- Claude API-based solutions for text processing
- Simple agent automations for repetitive tasks
- Expected time savings per week

### 5.2 Medium-Term Improvements (Implement within weeks)
- Custom Claude agent workflows
- MCP server integrations for tool connectivity
- AI-assisted decision making

### 5.3 Transformative Changes (Implement within months)
- End-to-end agentic workflows
- Custom AI agents for complete workflow segments
- System architecture recommendations

For EACH recommendation:
- Problem it solves (reference Section 4)
- How it works (specific Claude/AI capability)
- Implementation approach (tools, APIs, integrations needed)
- Expected impact (time saved, errors reduced)
- Prerequisites and dependencies
- Risk and guardrails needed

## 6. Prioritized Implementation Roadmap
- Ordered by impact-to-effort ratio
- Dependencies mapped
- Suggested phases
- Success metrics per phase
- Estimated cumulative time savings at each phase

## 7. Appendix
- Complete application inventory table
- Full workflow timeline with frame references
- Glossary of client-specific terms
- Pipeline metadata (frames analyzed, transcript word count, video duration)
```

## Deliverable 2 — Executive summary (1–2 pages)

Save to: `{DOCS_DIR}/{CLIENT_SLUG}-workflow-summary.md`

Contents:
- Who: {client-name} and their role context
- What: the workflow analyzed
- Key findings: top 5 insights
- Top 5 automation recommendations with expected impact
- Recommended next steps

Suitable for sharing with stakeholders who won't read the full report.
