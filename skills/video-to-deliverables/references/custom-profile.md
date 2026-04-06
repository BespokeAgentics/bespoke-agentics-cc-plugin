# Custom Profile

When `--profile custom --deliverables <list>` is used, the user selects specific deliverable types from the menu below. Compose Phase 2 by selecting only the agents needed to produce the requested deliverables.

## Available Deliverable Types

Each deliverable type maps to one or more agents. If a deliverable depends on another, include the dependency automatically.

### Standalone Deliverables (no dependencies beyond Phase 1)

| Deliverable ID | Description | Agent needed |
|---|---|---|
| `app-inventory` | Application/tool inventory | Application Inventory Agent |
| `workflow-timeline` | Chronological step-by-step process map | Workflow Timeline Agent |
| `friction-catalog` | Friction points and challenges catalog | Friction Catalog Agent |
| `screen-catalog` | Already produced in Phase 1 (no extra agent) | — |
| `meeting-topics` | Topics, decisions, key discussion points | Topic Extractor Agent |
| `action-items` | Action items with owners and deadlines | Action Item Tracker Agent |
| `procedure-steps` | Step-by-step procedural guide | Step Extractor Agent |
| `glossary` | Domain terms and definitions | Knowledge Mapper Agent |

### Dependent Deliverables

| Deliverable ID | Description | Dependencies |
|---|---|---|
| `automation-recs` | AI automation recommendations | Requires `friction-catalog` |
| `executive-summary` | 1-2 page executive summary | Requires at least one analysis deliverable |
| `feature-inventory` | Feature/requirement inventory | — (reads from Phase 1 + transcript) |
| `gap-analysis` | Gap analysis for migration | Requires `feature-inventory` + `platform-assessment` |
| `platform-assessment` | Target platform capability assessment | Requires `feature-inventory` |
| `ui-migration-map` | UI component migration mapping | — (reads from Phase 1) |
| `integration-assessment` | Integration/API assessment | — (reads from Phase 1) |
| `data-schema` | Data schema/object mapping | — (reads from Phase 1) |
| `transcript-analysis` | Deep transcript analysis | Requires transcript |

### Composite Deliverables (bundles)

| Deliverable ID | Expands to |
|---|---|
| `workflow-docs` | `app-inventory`, `workflow-timeline`, `friction-catalog` |
| `migration-docs` | `feature-inventory`, `platform-assessment`, `gap-analysis`, `ui-migration-map`, `integration-assessment`, `data-schema` |
| `meeting-docs` | `meeting-topics`, `action-items` |
| `training-docs` | `procedure-steps`, `glossary` |

---

## Constructing the Custom Pipeline

1. **Parse the `--deliverables` list**: Split by comma, resolve any composite deliverables into their components.

2. **Resolve dependencies**: For each deliverable, check if its dependencies are in the list. If not, add them automatically and inform the user: "Auto-adding `{dep}` as a dependency of `{deliverable}`."

3. **Build the wave structure**:
   - **Wave 1**: All deliverables with no dependencies (beyond Phase 1 outputs)
   - **Wave 2**: Deliverables that depend on Wave 1 outputs
   - **Wave 3**: Deliverables that depend on Wave 2 outputs (e.g., `executive-summary`)

4. **Launch agents** following the wave structure, using the agent prompts from the appropriate profile reference files.

5. **If `executive-summary` is requested**, it always runs last and reads ALL other deliverables produced.

---

## Agent Prompt Templates

For each deliverable type, use the corresponding agent prompt from these profile references:

- `app-inventory`, `workflow-timeline`, `friction-catalog`, `automation-recs`, `transcript-analysis` → `workflow-profile.md`
- `feature-inventory`, `platform-assessment`, `gap-analysis`, `ui-migration-map`, `integration-assessment`, `data-schema` → `migration-profile.md`
- `meeting-topics`, `action-items` → `meeting-profile.md`
- `procedure-steps`, `glossary` → `training-profile.md`

### Executive Summary Agent (universal)

```
Agent: "Generate executive summary"
Prompt: |
  Produce a 1-2 page executive summary for "{project-name}" ({label}).

  Read ALL deliverables produced in this pipeline run:
  {list all DOCS_DIR/*.md files produced}

  Structure:
  # {project-name}: {label} — Executive Summary
  *Generated [current date]*

  ## Overview (what was analyzed and why)
  ## Key Findings (top 5, drawn from all deliverables)
  ## Recommendations (top 5, if applicable)
  ## Next Steps

  Save to: {DOCS_DIR}/{PROJECT_SLUG}-executive-summary.md
```
