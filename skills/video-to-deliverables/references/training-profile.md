# Training Profile

Deliverable profile for extracting training and procedural documentation from video recordings. Ideal for turning screen recordings of processes into step-by-step guides, SOPs, knowledge base articles, and reference materials.

## Primary Deliverable
`{DOCS_DIR}/{PROJECT_SLUG}-procedure-guide.md`

## Wave Structure

```
Wave 1 (parallel): Step Extractor ∥ Knowledge Mapper
    ↓
Wave 2 (sequential): Documentation Synthesis
```

## Final Deliverables
- `{DOCS_DIR}/{PROJECT_SLUG}-procedure-guide.md` — Step-by-step procedure guide (primary)
- `{DOCS_DIR}/{PROJECT_SLUG}-quick-reference.md` — Quick reference card
- `{DOCS_DIR}/{PROJECT_SLUG}-knowledge-base.md` — Knowledge base article(s)
- `{DOCS_DIR}/{PROJECT_SLUG}-troubleshooting.md` — Common issues and solutions

---

## Wave 1 — 2 Parallel Agents

### Agent 1: Step-by-Step Extractor

```
Agent: "Extract procedural steps from recording"
Prompt: |
  Analyze the recording for "{project-name}" ({label}) to extract a precise step-by-step procedure.

  Read:
  - {DOCS_DIR}/screen-catalog.md
  - {DOCS_DIR}/component-library.md
  - {DOCS_DIR}/system-architecture-map.md
  - {FRAMES_DIR}/transcript.txt (if available)

  For each step in the demonstrated procedure:
  1. **Step number and title** — Clear, imperative action ("Click the Submit button", "Enter the customer ID")
  2. **Application context** — Which application and screen
  3. **Detailed instructions** — Exactly what to do, where to click, what to type
  4. **Expected result** — What should happen after this step
  5. **Visual reference** — Frame number/timestamp showing this step
  6. **Tips/warnings** — Anything the narrator mentions about gotchas, common mistakes, or tips
  7. **Prerequisites** — What must be true before this step (logged in, data available, etc.)
  8. **Decision points** — If the procedure branches ("If X, do Y; otherwise do Z")

  Pay close attention to the narrator's verbal cues — they often explain WHY a step matters, shortcuts, and common mistakes.

  Save to: {DOCS_DIR}/procedure-steps-{LABEL}.md
```

### Agent 2: Knowledge & Context Mapper

```
Agent: "Map domain knowledge and context"
Prompt: |
  Extract domain knowledge, terminology, and contextual information from the "{project-name}" ({label}) recording.

  Read:
  - {FRAMES_DIR}/transcript.txt (if available)
  - {DOCS_DIR}/screen-catalog.md
  - {DOCS_DIR}/component-library.md

  Document:
  1. **Glossary** — Domain-specific terms used, with definitions (from context or transcript)
  2. **Prerequisites** — What someone needs to know or have before starting this procedure
  3. **Common errors** — Mistakes mentioned or demonstrated, with corrections
  4. **Shortcuts and tips** — Efficiency tricks mentioned or demonstrated
  5. **Edge cases** — Special scenarios discussed ("If the customer is international...", "For bulk orders...")
  6. **Related procedures** — References to other processes that connect to this one
  7. **Access requirements** — Systems, permissions, or credentials needed

  Save to: {DOCS_DIR}/knowledge-context-{LABEL}.md
```

Wait for both agents to complete.

---

## Wave 2 — Documentation Synthesis

```
Agent: "Synthesize training documentation"
Prompt: |
  Produce final training deliverables for "{project-name}" ({label}).

  Read ALL:
  - {DOCS_DIR}/procedure-steps-{LABEL}.md
  - {DOCS_DIR}/knowledge-context-{LABEL}.md
  - {FRAMES_DIR}/transcript.txt (if available)

  Produce FOUR deliverables:

  ### 1. Procedure Guide (primary)
  Save to: {DOCS_DIR}/{PROJECT_SLUG}-procedure-guide.md

  # {project-name}: {label}
  *Procedure Guide*

  ## Overview (what this procedure accomplishes, when to use it)
  ## Prerequisites (access, knowledge, setup)
  ## Step-by-Step Procedure (numbered, detailed, with expected results)
  ## Decision Trees (for branching logic)
  ## Troubleshooting (common issues and solutions)
  ## Glossary
  ## Related Procedures

  Write in clear, second-person imperative ("Click...", "Enter...", "Verify...").
  Include frame references as [Screenshot: timestamp] markers for future screenshot insertion.

  ### 2. Quick Reference Card
  Save to: {DOCS_DIR}/{PROJECT_SLUG}-quick-reference.md

  A 1-page cheat sheet: condensed steps, keyboard shortcuts, key fields, common values.
  Designed to be printed or pinned. Minimal prose, maximum density.

  ### 3. Knowledge Base Article
  Save to: {DOCS_DIR}/{PROJECT_SLUG}-knowledge-base.md

  Written as a searchable KB article:
  - Problem/scenario description
  - Solution (the procedure, more concise than the full guide)
  - Related articles (cross-references)
  - Tags/categories for KB indexing

  ### 4. Troubleshooting Guide
  Save to: {DOCS_DIR}/{PROJECT_SLUG}-troubleshooting.md

  Common issues organized as:
  - Symptom (what the user sees)
  - Cause (why it happens)
  - Solution (step-by-step fix)
  - Prevention (how to avoid it)
```

Wait for synthesis to complete.
