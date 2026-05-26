# Steps 1–2 — Classify the document & identify affected pages

## Step 1 — Read and classify

Read the document at `{document-path}`. Extract:

### 1. Content summary

What is this document fundamentally about? Classify into one or more categories:

- **Decision** — "Client approved X approach"
- **Clarification** — "Detailed business rule for feature Y"
- **Scope change** — "Feature Z is now out of scope"
- **Risk alert** — "Integration with system X is at risk"
- **Evidence** — "Detailed description of current workflow"
- **Question** — "How should we handle X scenario?"
- **Approval / status update** — "Gap G1 resolution approved"

### 2. Entities mentioned

Catalog every wiki entity the document references:

- Features (by name or description)
- Gaps or risks
- Decisions
- Questions
- Integrations
- Systems or vendors

### 3. Key information

Extract the most important facts:

- New business rules or constraints.
- Decisions made.
- Problems identified.
- Commitments or approvals.
- Timeline implications.

## Step 2 — Identify affected wiki pages

For each entity mentioned:

1. **Normalize slug** — lowercase-hyphenated.
2. **Check wiki location** for an existing page at one of:
   - `wiki/clients/{company}/features/{slug}.md`
   - `wiki/clients/{company}/gaps/{slug}.md`
   - `wiki/clients/{company}/decisions/{slug}.md`
   - `wiki/clients/{company}/questions/{slug}.md`
3. **Assess impact** — what aspect of the page is affected?
   - Decision status changing (e.g. `ootb → custom`)?
   - Description needing clarification?
   - New evidence for or against an approach?
   - New contradiction discovered?
   - Question answered or escalated?

## Per-doc-type guidance

### Email
- Subject and date matter as metadata.
- Note sender / recipient if significant (e.g. "Client approved via email from CTO").
- Use the message timestamp where available.

### PDF
- Document title and version matter.
- Reference page numbers for longer PDFs.
- Extract tables and structured data carefully.

### Spec
- Version number and date are critical.
- Link to the spec's location or reference system.
- Note whether this is a client-provided spec or the team's own.

### Slack
- Include the message timestamp for traceability.
- Note thread depth (passing comment vs. full discussion).
- Slack is often informal — verify decisions against other sources before promoting.

### Other
- Note the document type clearly in logging.
- Ensure the source path is unambiguous.
