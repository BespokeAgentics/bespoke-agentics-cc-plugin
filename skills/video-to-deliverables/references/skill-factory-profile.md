# Skill-Factory Profile

Deliverable profile that reverse-engineers a technical video into an installable Claude Code plugin — a set of Skills, slash Commands, executable scripts, and (when complexity warrants) subagents. The user is interviewed _after_ content analysis so every decision is grounded in what the video actually shows.

Originally designed for technical talks and tutorials (e.g., a Neo4j graph-RAG walkthrough), but also supports conceptual / architecture talks (doc-only skills) and product demos (setup / integration skills derived from UI + narration).

## Primary Deliverable
`{PROJECT_DIR}/generated-plugin-{PLUGIN_SLUG}/plugin.json`

`PLUGIN_SLUG` is set during the Wave 2 interview (defaults to `PROJECT_SLUG-{LABEL}`).

## Wave Structure

```
Wave 1 (parallel):  Topic Decomposer ∥ Artifact Harvester ∥ External-Source Crawler
    ↓
Wave 2 (orchestrator + user): Findings-grounded interview via AskUserQuestion batches
    ↓
Wave 3 (parallel):  Skill Writer (×N) ∥ Command Writer ∥ Script Writer ∥ Agent Architect ∥ Plugin Scaffolder
    ↓
Wave 4 (parallel):  Schema Validator ∥ Dry-Run Runner ∥ Source-Grounding Auditor ∥ Skill-Creator Reviewer
```

Wave 1 and Wave 4 are run entirely by subagents. Wave 2 is conducted by the **parent orchestrator** using the `AskUserQuestion` tool — subagents cannot ask questions. Wave 3 is subagent-parallel.

## Intermediate Deliverables
- `{DOCS_DIR}/candidate-skills.md` — decomposed skill candidates (Wave 1)
- `{DOCS_DIR}/extracted-artifacts.md` — verbatim code/command/config extractions (Wave 1)
- `{DOCS_DIR}/external-references.md` — fetched URLs, web-search fills, GitHub repo material (Wave 1)
- `{DOCS_DIR}/interview-answers.json` — structured record of user answers (Wave 2)
- `{DOCS_DIR}/skill-factory-validation.md` — quality-gate findings (Wave 4)

## Final Deliverables (generated plugin)
All under `{PLUGIN_DIR} = {PROJECT_DIR}/generated-plugin-{PLUGIN_SLUG}/`:
- `{PLUGIN_DIR}/plugin.json` — plugin manifest (primary)
- `{PLUGIN_DIR}/README.md` — plugin overview, install instructions, source video citation
- `{PLUGIN_DIR}/skills/{skill-name}/SKILL.md` — one per user-selected skill
- `{PLUGIN_DIR}/skills/{skill-name}/scripts/*` — executable scripts (when user promoted artifacts)
- `{PLUGIN_DIR}/skills/{skill-name}/references/*.md` — supporting reference material
- `{PLUGIN_DIR}/commands/{plugin-slug}:{command}.md` — slash commands (orchestration + per-skill entry points)
- `{PLUGIN_DIR}/agents/*.md` — subagents when the Agent Architect runs

---

## Wave 1 — 3 Parallel Agents

All three read from Phase 1 synthesis outputs and run in parallel.

### Agent 1: Topic Decomposer

```
Agent: "Decompose video into candidate skills"
Prompt: |
  You are decomposing the video analysis for "{project-name}" ({label}) into a menu of candidate skills that could be generated from the content.

  Read:
  - {DOCS_DIR}/screen-catalog.md
  - {DOCS_DIR}/component-library.md
  - {DOCS_DIR}/system-architecture-map.md
  - {FRAMES_DIR}/transcript.txt (if available)
  - {DOCS_DIR}/frame-analysis-chunk-*.md (for any nuance the synthesis flattened)

  First, classify the video mode:
  - `hands-on` — screen recording dominated by commands, code, configs, CLI output (e.g., a tutorial walkthrough)
  - `architecture` — slides/whiteboard dominated, few or no terminal/code screens
  - `product-demo` — vendor UI walkthrough, little or no code but clear setup/integration steps
  - `mixed` — if two modes have roughly equal screen time

  Then produce {DOCS_DIR}/candidate-skills.md with this structure:

  # Candidate Skills

  **Video mode:** {mode}
  **Primary domain:** {e.g., "Graph databases / RAG"}
  **Source video:** {video-path or URL}

  ## Candidates

  For each candidate skill, include:

  ### {candidate-id: kebab-case slug}
  - **Proposed name:** e.g., `neo4j-rag:graph-setup`
  - **One-line description:** what the skill does, why someone would invoke it
  - **Trigger phrases:** 3-5 natural-language phrases that should route to this skill
  - **Source timestamps:** list of frame-range or transcript timestamps the skill is grounded in
  - **Coverage:** what topics in the video this skill encompasses
  - **Systems/tools touched:** e.g., Docker, Neo4j, Python, OpenAI API
  - **Confidence:** High / Medium / Low — how completely the video covers this topic
  - **Depends on:** other candidate-ids it needs to run first (or "none")
  - **Suggested kind:** `executable` (has runnable scripts), `reference` (documentation only), `orchestration` (chains other skills)

  Aim for 2-7 candidates. Too few wastes the multi-skill decomposition; too many dilutes each skill. If the video is narrow, fewer is honest. Flag when there's one strong candidate and several weak ones.

  Also include:
  ## Suggested Plugin Identity
  - **Plugin slug:** kebab-case derived from video title or dominant topic
  - **Plugin namespace:** same as slug by default
  - **Plugin description:** 1-2 sentences
  - **Why these skills hang together:** the thesis that makes this a plugin, not a pile
```

### Agent 2: Artifact Harvester

```
Agent: "Harvest verbatim code, commands, and configs"
Prompt: |
  Re-read every frame tagged as code, terminal, or config in the Phase 1 analysis for "{project-name}" ({label}). Extract each block VERBATIM — character-for-character as visible on screen.

  Read:
  - {FRAMES_DIR}/manifest.json (to find frame file paths)
  - {DOCS_DIR}/frame-analysis-chunk-*.md (to identify which frames showed code/terminal/config)
  - {FRAMES_DIR}/transcript.txt (for surrounding narration at each timestamp)

  For each code/command/config block visible in a frame, use the Read tool on the frame PNG and transcribe the full visible content into a code fence. If a block spans multiple consecutive frames (presenter scrolls, or code builds up), capture the FINAL visible state and note any earlier partial states.

  Save output to: {DOCS_DIR}/extracted-artifacts.md

  Format each entry as:

  ## Artifact {N}
  - **Type:** bash | python | yaml | cypher | sql | json | dockerfile | js | ts | other (specify)
  - **Source frame(s):** frame_00042.png (and any consecutive frames showing the same block)
  - **Timestamp:** MM:SS (or range MM:SS – MM:SS)
  - **On-screen title/filename:** the filename shown in the editor tab or terminal prompt, if visible
  - **Narrator context:** 1-2 sentences of surrounding transcript quoting what the presenter said while the block was visible
  - **Suggested target skill:** candidate-id from candidate-skills.md this block belongs to (the orchestrator maps these — you can leave as "?" if unclear)
  - **Content:**
    ```{type}
    <verbatim block>
    ```
  - **Transcription confidence:** High / Medium / Low — flag frames where text was blurry, partially obscured, or cut off
  - **Notes:** anything suspicious (truncation, small font, flash-frame content)

  If you cannot confidently read a block, include what you can and mark Low confidence with a note. Do NOT re-synthesize or guess — leave gaps explicit so the interview can surface them.

  At the end of the file, add:
  ## Harvest Summary
  - Total artifacts: N
  - By type: {type counts}
  - Low-confidence count: N
  - Frames re-read: N
```

### Agent 3: External-Source Crawler

```
Agent: "Mine external sources referenced by the video"
Prompt: |
  Extract and fetch every external resource the video points at, for "{project-name}" ({label}).

  Read:
  - {FRAMES_DIR}/transcript.txt (if available)
  - {DOCS_DIR}/frame-analysis-chunk-*.md
  - {DOCS_DIR}/component-library.md

  Step 1 — Enumerate references. Find:
  - URLs shown on screen (docs sites, blog posts, landing pages)
  - URLs spoken in transcript ("go to github.com/...")
  - GitHub repos mentioned or shown
  - Package names mentioned (npm, pip, cargo) with their canonical docs pages
  - Product/company names that have well-known documentation (e.g., "the Neo4j APOC library")

  Step 2 — Fetch. For each reference:
  - URLs: use WebFetch with a focused prompt about what the video was demonstrating on that page
  - GitHub repos: use WebFetch on the repo's README; if a specific file was shown, also fetch that file's raw URL
  - Missing specifics the video skimmed over (e.g., "the full APOC install command"): use WebSearch, fetch the top official-docs result

  Step 3 — Log everything. Save to: {DOCS_DIR}/external-references.md

  Format each entry as:

  ## Reference {N}: {short name}
  - **Type:** shown-url | spoken-url | github-repo | package-docs | web-search-fill
  - **Source:** where in the video it was referenced (frame/timestamp, or "transcript at MM:SS", or "web-search for X")
  - **URL:** canonical URL
  - **Fetch status:** fetched | failed | skipped-restricted
  - **Provenance tag:** video | fetched | web-search — used downstream to distinguish video-grounded facts from augmentations
  - **Relevance:** 1-sentence note on what this source contributes
  - **Key content:** the specific facts, commands, or snippets from the source that are relevant to the candidate skills (concise extraction — not the whole page)
  - **Suggested target skill:** candidate-id from candidate-skills.md, or "general" if multi-skill

  If WebFetch is blocked (403, login-walled, restricted domain), mark skipped-restricted and note it. Do NOT try alternate fetching methods.

  At the end:
  ## Crawl Summary
  - References enumerated: N
  - Fetched successfully: N
  - Skipped/failed: N (list them)
  - By provenance: video-grounded N, fetched N, web-search N
```

Wait for ALL THREE Wave 1 agents to complete before proceeding. Verify all three output files exist and are non-empty.

---

## Wave 2 — Findings-Grounded Interview (Orchestrator + User)

The orchestrator (you, the parent) conducts this directly using `AskUserQuestion`. Do **not** dispatch this to a subagent — subagents cannot talk to the user.

### Step 1: Load findings

Read all three Wave 1 outputs:
- `{DOCS_DIR}/candidate-skills.md`
- `{DOCS_DIR}/extracted-artifacts.md`
- `{DOCS_DIR}/external-references.md`

Also skim `{DOCS_DIR}/screen-catalog.md` and `{DOCS_DIR}/system-architecture-map.md` for context.

### Step 2: Print a findings digest to the user

Before any questions, print a human-readable summary:

```
=== Skill-Factory Findings ===
Video mode:        {mode}
Candidate skills:  {N} (see {DOCS_DIR}/candidate-skills.md)
Extracted artifacts: {N} verbatim code/command/config blocks ({low-confidence-count} flagged low-confidence)
External references: {N} fetched, {N} skipped
Primary domain:    {from candidate-skills.md}

I'll ask a short series of grounded questions to decide what to build.
```

### Step 3: Run the interview batches

Ask the following `AskUserQuestion` batches in order. Later batches depend on earlier answers, so do them sequentially (one `AskUserQuestion` call per batch, waiting for the answer).

**Batch 1 — Plugin Identity** (1 AskUserQuestion call, 2-3 questions)

- Q: "What should the plugin slug be?" — present the decomposer's suggestion as the first (recommended) option, plus 1-2 alternatives derived from the video title, plus an "Other" free-text path. `header: "Plugin slug"`.
- Q: "What target environment should generated skills assume?" — options: `Local dev (macOS/Linux)`, `Docker`, `Cloud (managed service)`, `All three — parameterize`. `header: "Target env"`.
- Q: "What audience are these skills for?" — options: `Me / my team (Recommended)`, `Open source (others will install it)`, `Internal consulting engagement`. `header: "Audience"`. Affects README tone, license boilerplate, whether examples can reference personal paths.

**Batch 2 — Which Skills to Build** (1 AskUserQuestion call, 1 question, `multiSelect: true`)

- Q: "Which candidate skills do you want to generate?" — one option per entry in `candidate-skills.md`, in the order they appear. Each option's `description` repeats the one-liner + confidence level + suggested kind. Include a "Select all" nudge in the question text but let the user pick explicitly. `header: "Skills to build"`, `multiSelect: true`.

If the user picks fewer than the total, record which were dropped and skip their artifacts / external refs in later waves.

**Batch 3 — Depth & Orchestration** (1 AskUserQuestion call, 2 questions)

- Q: "What depth should the generated skills target?" — `Quickstart (minimum to run)`, `Standard (covers the video)`, `Comprehensive (video + fetched external docs)`. `header: "Depth"`. Affects how much external-reference material ends up in each skill vs. referenced as links.
- Q: "Should the plugin include an orchestration slash command that chains the skills?" — `Yes (Recommended)`, `No — skills only`, `Yes, and also per-skill commands`. `header: "Orchestration"`.

**Batch 4 — Subagents?** (1 AskUserQuestion call, 1 question)

Decide the default based on complexity: if any selected skill has ≥2 sequential steps in its extracted-artifacts entries OR if multiple skills have `depends on` relationships, default to "Yes". Otherwise default to "No".

- Q: "Should the plugin include subagents?" — `Yes — let Agent Architect decide per skill (Recommended)`, `Yes — one orchestrator agent only`, `No — skills and scripts only`. `header: "Agents?"`.

**Batch 5 — Artifact Confirmation** (loop: one AskUserQuestion call per selected skill)

For each selected skill, gather the artifacts tagged to it in `extracted-artifacts.md`. If there are artifacts, ask a single `multiSelect: true` question. Each option is one artifact — use the `preview` field to render the verbatim code block so the user can inspect it. `description` carries the narrator context + transcription confidence.

- Q: "For `{skill-name}`, which extracted artifacts should become executable scripts in the generated skill?" — options are individual artifacts. Unchecked artifacts are still cited in the SKILL.md body (as reference material) but don't get materialized as scripts.
- `header: "{skill-slug} artifacts"` (truncated to 12 chars).

Low-confidence artifacts should have that noted in their `description`. If there are zero artifacts for a skill, skip this batch for that skill (it'll be a reference-only skill).

**Batch 6 — External Augmentations** (1 AskUserQuestion call, 1 question, `multiSelect: true`)

- Q: "Which external sources should be embedded as reference material in the plugin?" — list every entry in `external-references.md` that was successfully fetched. Each option's `description` shows the provenance tag (video / fetched / web-search) and the 1-sentence relevance note. Default selections: all `video`-provenance entries pre-checked, `fetched` pre-checked, `web-search` unchecked. `header: "External refs"`.

Unchecked refs are dropped from Wave 3.

### Step 4: Persist answers

Write `{DOCS_DIR}/interview-answers.json` with this shape:

```json
{
  "plugin": {
    "slug": "...",
    "namespace": "...",
    "description": "...",
    "target_env": "...",
    "audience": "...",
    "author": "<from `git config user.name` if available, else empty>",
    "version": "0.1.0"
  },
  "selected_skills": [
    {
      "candidate_id": "...",
      "name": "...",
      "description": "...",
      "trigger_phrases": [...],
      "kind": "executable | reference | orchestration",
      "depth": "quickstart | standard | comprehensive",
      "selected_artifacts": ["artifact-N", ...],
      "depends_on": [...]
    }
  ],
  "orchestration_command": true,
  "per_skill_commands": false,
  "include_subagents": true,
  "selected_external_refs": ["ref-N", ...],
  "dropped_candidates": [...],
  "video_source": {
    "path_or_url": "...",
    "mode": "hands-on | architecture | product-demo | mixed"
  }
}
```

Also print a one-paragraph recap to the user: "Got it. Generating `{plugin-slug}` with {N} skills ({list}), {orchestration / no orchestration}, {with / without} subagents. Running Wave 3 now."

---

## Wave 3 — Parallel Generation

Read `{DOCS_DIR}/interview-answers.json` and launch the following agents in parallel. Each agent gets a subset of the answers JSON + the Wave 1 outputs it needs.

`PLUGIN_DIR = {PROJECT_DIR}/generated-plugin-{plugin.slug}`

Create `{PLUGIN_DIR}/` and its subdirectories (`skills/`, `commands/`, `agents/`, `references/`) before launching.

### Templates

Wave 3 agents should prefer the templates at `${CLAUDE_PLUGIN_ROOT}/skills/video-to-deliverables/templates/` as starting shapes and substitute the placeholders (`{{VARIABLE}}`) with values from `interview-answers.json` + the Wave 1 outputs:

- `plugin.json.tmpl` → plugin manifest
- `README.md.tmpl` → plugin overview
- `SKILL.md.tmpl` → per-skill body
- `command.md.tmpl` → slash command
- `script-bash.sh.tmpl` / `script-python.py.tmpl` → per-artifact scripts
- `sources.md.tmpl` → provenance trail per skill

The templates use `{{VAR}}` mustache-style markers — agents should substitute and strip `{{#each}}` / `{{#if}}` control blocks by expanding inline. The templates are guides, not strict contracts; diverge when the video's specifics warrant it.

### Agent 3a: Plugin Scaffolder (launch first, others depend on directory structure)

Actually scaffold the plugin skeleton so sibling agents can write into it without racing. Run this sequentially before the parallel batch.

```
Agent: "Scaffold plugin directory structure"
Prompt: |
  Create the plugin skeleton at {PLUGIN_DIR}.

  Read: {DOCS_DIR}/interview-answers.json

  Produce:
  1. {PLUGIN_DIR}/plugin.json — plugin manifest. Use this shape:
     {
       "name": "<plugin.slug>",
       "version": "<plugin.version>",
       "description": "<plugin.description>",
       "author": { "name": "<plugin.author>" },
       "skills": ["./skills/<name>" for each selected_skill],
       "commands": ["./commands/..." ],
       "agents": ["./agents/..."]   // omit if !include_subagents
     }

  2. {PLUGIN_DIR}/README.md — structured as:
     # {plugin-name}
     {description}

     ## Source
     Generated from video: {video_source.path_or_url}
     Video mode: {video_source.mode}
     Generated on: {today's date}

     ## Skills
     (one bullet per selected_skill: name — description)

     ## Install
     Drop into your Claude Code plugin marketplace or reference via {CLAUDE_PLUGIN_ROOT} in your settings.

     ## Provenance
     Each skill cites frame timestamps and external URLs that grounded its content. See skills/*/references/sources.md for the full provenance trail.

  3. Empty subdirectories: {PLUGIN_DIR}/skills/, {PLUGIN_DIR}/commands/, {PLUGIN_DIR}/references/. Also {PLUGIN_DIR}/agents/ if include_subagents is true.

  Do not write the actual skill/command/agent contents — those are handled by the parallel agents in the next step.
```

Wait for the scaffolder to complete. Then launch the parallel batch:

### Agent 3b: Skill Writer (one per selected skill, parallel)

For each entry in `selected_skills`, launch a Skill Writer:

```
Agent: "Generate SKILL.md for {skill-name}"
Prompt: |
  You are generating a SKILL.md and supporting files for the skill "{skill.name}" in the plugin "{plugin.slug}".

  Target directory: {PLUGIN_DIR}/skills/{skill.name-sans-namespace}/

  Read:
  - {DOCS_DIR}/interview-answers.json (your slice: selected_skills[*] where candidate_id == "{skill.candidate_id}")
  - {DOCS_DIR}/candidate-skills.md (section for your candidate)
  - {DOCS_DIR}/extracted-artifacts.md (artifacts tagged to your candidate OR in selected_artifacts)
  - {DOCS_DIR}/external-references.md (entries in selected_external_refs tagged to your candidate or "general")
  - {FRAMES_DIR}/transcript.txt (for timestamp grounding and direct quotes)

  Produce these files:

  1. {PLUGIN_DIR}/skills/{skill-name}/SKILL.md
     - YAML frontmatter:
         name: {skill.name}
         description: "{triggering description — include the trigger phrases naturally, follow skill-creator conventions}"
     - Body structure:
         <objective>
         One-paragraph statement of what this skill does and when to invoke it.
         </objective>

         <arguments>
         (only if this skill takes arguments — otherwise omit)
         </arguments>

         <prerequisites>
         Required tools, env vars, credentials. Derived from video + fetched docs.
         </prerequisites>

         <procedure>
         Numbered steps. Each step grounded in a specific frame timestamp or artifact.
         Reference scripts via: ${CLAUDE_PLUGIN_ROOT}/skills/{skill-name}/scripts/<script>
         </procedure>

         <validation>
         How to confirm the procedure worked. Grounded in what the video shows after each step.
         </validation>

         <references>
         Links to references/*.md and external URLs.
         </references>

  2. For each entry in selected_artifacts that belongs to this skill, write a script file to {PLUGIN_DIR}/skills/{skill-name}/scripts/<inferred-filename>.
     - Include a shebang appropriate to the type (bash → #!/usr/bin/env bash, python → #!/usr/bin/env python3).
     - At the top, include a comment block citing the source: # Source: frame {N}, timestamp {MM:SS}, video {video-path}
     - Include the verbatim content from extracted-artifacts.md.
     - Add minimal arg parsing if the script has hard-coded values the user will want to override (document these with comments — don't fabricate behavior the video didn't show).
     - chmod is not needed here; the plugin consumer handles it.

  3. {PLUGIN_DIR}/skills/{skill-name}/references/sources.md
     - Bulleted list of every frame timestamp and external URL cited in SKILL.md.
     - Each bullet tags provenance: [video] for frame-grounded, [fetched] for external docs, [web-search] for search-fills.

  4. For each selected_external_refs tagged to this skill with depth == "comprehensive" or "standard", copy the key-content section verbatim into {PLUGIN_DIR}/skills/{skill-name}/references/<short-name>.md with a header linking to the canonical URL.

  Hard rules:
  - Every executable claim ("run X", "set Y to Z") must be traceable to a frame timestamp or a fetched-source URL. If you can't ground it, don't assert it — caveat with "the video did not show…".
  - Don't invent flags, options, or behaviors not shown or documented.
  - For video_source.mode == "architecture", the skill is reference-only: omit scripts, keep procedure as prose explaining concepts with frame citations.
  - For video_source.mode == "product-demo", scripts may be rare — UI steps become numbered procedure steps with frame-timestamp citations.
```

### Agent 3c: Command Writer (parallel with Skill Writers)

```
Agent: "Generate slash commands"
Prompt: |
  Generate the slash-command markdown files for plugin "{plugin.slug}".

  Read:
  - {DOCS_DIR}/interview-answers.json
  - All candidate-skills entries the user selected

  If orchestration_command is true:
    Write {PLUGIN_DIR}/commands/{plugin.slug}:run.md
    - Frontmatter: description (what the orchestration does), argument-hint (typical args)
    - Body: explains that invoking this command chains the selected skills in dependency order
    - Include an <arguments> block matching what the skills need (union of arg shapes)
    - Include example invocations

  If per_skill_commands is true:
    For each selected_skill, write {PLUGIN_DIR}/commands/{plugin.slug}:{skill-short-name}.md
    - Routes to the corresponding skill
    - Includes the skill's description and an example

  Every command file must cite the generating video in a footer comment block.
```

### Agent 3d: Agent Architect (parallel, conditional)

Only launch if `include_subagents == true`.

```
Agent: "Scaffold subagents for the plugin"
Prompt: |
  Determine which selected skills warrant subagents and scaffold them.

  Read:
  - {DOCS_DIR}/interview-answers.json
  - ${CLAUDE_PLUGIN_ROOT}/skills/architect-agents/SKILL.md (apply its conventions)
  - {PLUGIN_DIR}/skills/*/SKILL.md (the newly generated skills — they may not be ready yet; use interview-answers.json as authority)

  For each selected_skill where:
  - extracted_artifacts has ≥2 ordered steps (the skill has a meaningful pipeline), OR
  - skill.depends_on includes other selected skills (it orchestrates them)

  Generate {PLUGIN_DIR}/agents/{skill-short-name}-orchestrator.md using architect-agents' orchestrator-agent template.

  Also generate {PLUGIN_DIR}/agents/{plugin.slug}-coordinator.md if orchestration_command is true — the top-level coordinator that chains skills.

  If no skills meet the criteria, write nothing and output "No subagents warranted for this plugin — skills are simple enough to invoke directly."
```

### Agent 3e: Script Writer — handled inside Agent 3b

Note: the Skill Writer agent already materializes scripts as part of its skill package. A separate Script Writer is not launched.

Wait for ALL Wave 3 agents to complete before Wave 4.

---

## Wave 4 — Quality Gates (4 parallel agents)

All read from the generated plugin directory. Results converge into `{DOCS_DIR}/skill-factory-validation.md`.

### Agent 4a: Schema Validator

```
Agent: "Validate plugin file schemas"
Prompt: |
  Validate the generated plugin at {PLUGIN_DIR} for schema correctness.

  Checks:
  1. {PLUGIN_DIR}/plugin.json parses as valid JSON and has required fields: name, version, description, skills.
  2. Every {PLUGIN_DIR}/skills/*/SKILL.md has parseable YAML frontmatter with `name` and `description` fields.
  3. Every SKILL.md `name` field matches the directory it lives in.
  4. Every command file in {PLUGIN_DIR}/commands/ has valid frontmatter and the command name matches {plugin.slug}:{x}.
  5. Every referenced script path (in SKILL.md body) actually exists under scripts/.
  6. Every referenced references/*.md actually exists.
  7. No unsubstituted placeholders of the form {variable-name} or ${CLAUDE_PLUGIN_ROOT} embedded in content that should have been replaced.

  Output findings to {DOCS_DIR}/skill-factory-validation.md under a "## Schema Validation" section. Use:
    ✓ check passed
    ⚠ warning (non-blocking)
    ✗ error (blocking)
  For each error or warning, include file path + line reference + fix suggestion.
```

### Agent 4b: Dry-Run Runner

```
Agent: "Dry-run extracted scripts"
Prompt: |
  Attempt to syntactically validate every generated script without executing destructive behavior.

  For each file in {PLUGIN_DIR}/skills/*/scripts/:
    - Bash scripts: run `bash -n <script>` to parse-check.
    - Python scripts: run `python3 -m py_compile <script>` to compile-check.
    - Try `<script> --help` or `<script> --dry-run` ONLY if the script supports it (detect by grepping the script for those flags). Never invoke a script that might alter the system.
    - Docker/compose files: run `docker compose config --quiet` if docker is available; otherwise note "docker not installed, skipping".
    - YAML/JSON configs: use yamllint or `python -c "import yaml; yaml.safe_load(open(...))"` / `jq .` to parse-check.

  Skip files that require external services you can't reach (Neo4j, OpenAI, etc.) — only check syntax and parse-time validity.

  Append findings to {DOCS_DIR}/skill-factory-validation.md under "## Dry-Run Results". For every failure, cite:
  - Script path
  - Error output
  - Likely cause (OCR error from verbatim extraction? Missing shebang? Indentation?)
  - Whether it's recoverable (user can fix) or indicates a bad extraction (Agent 2 must re-harvest)
```

### Agent 4c: Source-Grounding Auditor

```
Agent: "Audit source grounding"
Prompt: |
  For every executable claim in the generated skills, confirm traceability to the source video or fetched documentation.

  Read:
  - Every {PLUGIN_DIR}/skills/*/SKILL.md
  - {PLUGIN_DIR}/skills/*/references/sources.md
  - {DOCS_DIR}/extracted-artifacts.md
  - {DOCS_DIR}/external-references.md
  - {FRAMES_DIR}/transcript.txt

  For each claim in each SKILL.md (a "claim" is any imperative step, parameter value, or command to run):
  - If the claim cites a frame timestamp: verify the frame range exists in the manifest and the extracted-artifacts entry for that frame supports the claim.
  - If the claim cites an external URL: verify it appears in external-references.md with fetch_status = fetched.
  - If the claim has no citation: flag as "ungrounded assertion".

  Append findings to {DOCS_DIR}/skill-factory-validation.md under "## Grounding Audit". For each ungrounded or weakly-grounded claim:
  - File + line
  - The claim text
  - Nearest related citation (if any)
  - Recommendation: add citation, soften to caveat, or remove

  Note: ungrounded claims are warnings, not errors. Some skills will have synthesis statements that legitimately interpret the video rather than directly citing it. Use judgment — flag confident assertions without grounding, not obvious paraphrasing.
```

### Agent 4d: Skill-Creator Reviewer

```
Agent: "Review generated skills with skill-creator conventions"
Prompt: |
  Apply the skill-creator skill's conventions to every generated SKILL.md.

  Read:
  - The skill-creator skill at ${CLAUDE_PLUGIN_ROOT}/../anthropic-skills/skills/skill-creator/SKILL.md (or wherever it's installed — search common locations)
  - Every {PLUGIN_DIR}/skills/*/SKILL.md

  For each SKILL.md, evaluate:
  - Description triggers: does the description include natural-language phrases a user would actually say? Are trigger phrases concrete and non-overlapping with other skills in the plugin?
  - Structure: is the body well-organized (objective → prerequisites → procedure → validation)?
  - Naming: does the `name` field match plugin conventions (namespace:slug)?
  - Argument handling: if the skill takes arguments, are they documented?
  - Clarity: are steps imperative and actionable? Are frame references preserved but not overwhelming?

  Append findings to {DOCS_DIR}/skill-factory-validation.md under "## Skill-Creator Review".

  For each skill, give a short paragraph of feedback plus severity rating (ship-ready / minor-polish / needs-revision).
```

Wait for all four validators to complete. Read `{DOCS_DIR}/skill-factory-validation.md` and print a top-level summary to the user:

```
=== Skill-Factory Validation Summary ===
Schema:   {N} pass / {N} warn / {N} error
Dry-run:  {N} pass / {N} warn / {N} error
Grounding: {N} grounded / {N} caveated / {N} ungrounded
Review:   {N} ship-ready / {N} minor-polish / {N} needs-revision

{N} blocking issues. {"Plugin shipped to" if clean else "Fix the blocking issues above and re-run; plugin left at"} {PLUGIN_DIR}/.
```

If there are blocking errors (✗), note them but do not auto-fix. The user reviews and either accepts, fixes manually, or reruns with `--force`.

---

## Video-Mode Adaptations

The Topic Decomposer classifies the video mode. Wave 3 and Wave 4 adapt:

| Mode | Wave 3 adaptation | Wave 4 adaptation |
|---|---|---|
| `hands-on` | Full pipeline: scripts + SKILL bodies with executable procedures | All four gates run |
| `architecture` | Skills are reference-only (no scripts/); procedure sections are prose explanations grounded in slide frames | Dry-Run Runner skipped (nothing to run); grounding auditor tolerates more synthesis |
| `product-demo` | Scripts rare; procedures are UI-step walkthroughs with frame citations; emphasize prerequisites and account setup | Dry-Run Runner only validates any config files; grounding auditor treats UI steps as grounded when frame exists |
| `mixed` | Per-skill: executable skills get the hands-on treatment, reference skills get the architecture treatment | All four gates run; grounding tolerance varies per skill kind |

The Skill Writer agent is passed `video_source.mode` and `skill.kind` and routes accordingly.
