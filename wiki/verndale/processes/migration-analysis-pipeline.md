---
type: entity
client: shared
status: active
category: process
created: 2026-04-06
updated: 2026-04-06
sources:
  - ../../.claude/agents/migration-pipeline.md
  - ../../BostonBeerCompany/CLAUDE.md
tags:
  - process
  - methodology
  - ai-pipeline
---

# Verndale AI-Powered Migration Analysis Pipeline

## Overview

The Verndale migration analysis pipeline is an end-to-end orchestration system that transforms raw client meeting artifacts (video recordings, transcripts, or documents) into comprehensive Salesforce B2B Commerce gap analyses and client deliverables. The pipeline executes across six sequential phases, coordinating a specialized 16-skill agent team to extract features, identify gaps, validate technical feasibility, and prepare clients for design and implementation.

The pipeline is designed for iterative learning: each client engagement produces a Feature Inventory increment, and as more meetings occur, the gap analysis evolves into a living document that captures the full scope of the migration.

### Pipeline Phases (0-6)

**Phase 0: Artifact Preparation**
Raw meeting inputs (video or transcript) are decomposed into structured artifacts. Video files are processed to extract frames, audio, and metadata; transcripts are validated and prepared for downstream analysis.

**Phase 1: Parallel Analysis**
Multiple analysis streams run in parallel: frame analysis catalogs UI components and navigation patterns; meeting/transcript analysis extracts business capabilities, user roles, and integration requirements.

**Phase 2: Synthesis & Assessment**
Outputs from Phase 1 are merged and assessed against Salesforce B2B Commerce capabilities. Four specialized agents map features to OOTB options, identify custom development needs, assess UI migration paths, and design data schemas.

**Phase 3: Gap Analysis**
All Phase 2 findings are synthesized into a comprehensive, client-centric gap analysis organized by business workflow rather than platform feature list.

**Phase 4: Validation**
Salesforce claims in the gap analysis are fact-checked against current documentation, Trailhead, release notes, and AppExchange solutions using web search.

**Phase 5: Client Deliverables**
Prioritized Q&A documents and meeting preparation guides are produced, along with Confluence-compatible exports for immediate team handoff.

**Phase 6: Summary**
A pipeline summary report documents phases completed, documents generated, key statistics (features found, gaps identified, validations performed), confidence levels, and recommended next steps.

---

## Agent Team Architecture

The pipeline coordinates 16 specialized skills, each with a narrowly scoped role. This modular design enables parallel execution, fault isolation, and iterative improvement of individual agents without affecting the overall pipeline.

### Phase 0: Preprocessing Agents

**P1. Video Frame Extractor** (`extract-video-frames`)
- Extracts PNG frames from raw video files at configurable intervals (default: 1 frame/sec; recommended 5 sec for meetings)
- Extracts per-frame AAC audio segments aligned 1:1 with frames
- Produces continuous `full_audio.aac` track for full-length transcription
- Outputs `manifest.json` with timestamps, frame paths, and audio paths
- Requires `ffmpeg` on host machine

**P2. Frame Deduplicator** (`dedupe-frames`)
- Removes near-duplicate frames using perceptual hashing (dhash)
- Compares consecutive frames by Hamming distance; drops visually identical frames
- Typically reduces frame count by 50-80% for meeting recordings (e.g., 209 → 94 frames)
- Updates `manifest.json` with unique frames; saves original as `manifest.original.json`
- Produces `dedup-report.json` with per-frame decisions and distance statistics
- Enables downstream frame analysts to stay within context limits

**P3. Audio Transcriber** (`elevenlabs-transcribe`)
- Takes `full_audio.aac` from Phase 0 and sends to ElevenLabs Scribe v2 API
- Returns speaker-diarized transcript with audio event tagging (laughter, applause, etc.)
- Supports domain-specific vocabulary biasing (e.g., "MerchTank", "co-op billing")
- Requires `ELEVENLABS_API_KEY` in `.env` and `uv` installed

### Phase 1: Analysis Agents

**1. Transcript Analyst** (`transcript-analyst`)
- Accepts raw text transcripts from any source (Teams, Zoom, hand-typed notes, .vtt, .srt)
- Extracts features, business rules, user roles, pain points, integration hints, and domain terminology
- Rates confidence per feature (High/Medium/Low) and generates follow-up questions
- Produces Feature Inventory + Transcript Analysis Summary
- Works with zero visual artifacts (transcript-only option)

**2. Meeting Analyst** (`meeting-analyst`)
- Processes meeting transcripts combined with video frames and frame synthesis outputs
- Produces Feature Inventory documents with richer context than transcript-only analysis
- Extracts pain points, business rules, and integration hints from visual evidence and dialogue

**3. Frame Analyst** (`frame-analyst`) — Parallel Deployment
- Deployed as 5 parallel instances, each assigned ~42 frames (~3.5 minutes of demo)
- Visually inspects every frame: catalogs UI components, form fields, data tables, navigation, on-screen text, buttons, interaction patterns
- Produces per-chunk structured visual inventories
- Designed for exhaustive visual extraction without interpretation for Salesforce

**4. Frame Synthesis** (`frame-synthesis`)
- Merges 5 parallel Frame Analyst outputs into unified deliverables
- Deduplicates screens appearing across chunk boundaries
- Produces: Screen Catalog, Component Library, and System Architecture Map

### Phase 2: Assessment & Synthesis Agents

**5. SFCC B2B Expert** (`sfcc-b2b-expert`)
- Maps features from Feature Inventory to Salesforce B2B Commerce capabilities
- Assesses config-only vs. custom development needs
- Provides implementation guidance and effort estimates
- Evaluates AppExchange solutions and alternatives

**6. UI Migration Agent** (`ui-migration`)
- Consumes Screen Catalog and Component Library from Frame Synthesis
- Maps current UI components to Salesforce Experience Cloud / LWC equivalents
- Identifies UX gaps and improvement opportunities
- Produces UI Migration Map

**7. Integration/API Agent** (`integration-api`)
- Catalogs all integration points and external dependencies discovered
- Designs Salesforce integration architecture (APIs, middleware, data flows)
- Assesses integration risks, performance, and failure handling
- Produces Integration Assessment

**8. Data Schema Agent** (`data-schema`)
- Consumes System Architecture Map from Frame Synthesis
- Maps discovered data entities and relationships to Salesforce standard and custom objects
- Outlines data migration strategy and volume/performance considerations
- Produces Data Schema Mapping document

### Phase 3: Core Analysis

**9. Gap Analysis Agent** (`gap-analysis`)
- Synthesizes all Phase 2 outputs into a comprehensive gap analysis
- Organizes findings by **client business workflow** (not platform features)
- Produces core deliverable: `docs/gap-analysis-{company}-{date}.md`
- Includes: gap severity, resolution options, effort estimates, confidence levels
- Traces each gap back to discovered features and business context

### Phase 4: Validation

**10. SFCC Validator** (`sfcc-validator`)
- Reads completed gap analysis and all Salesforce capability claims
- Uses web search to validate against current Salesforce documentation, Trailhead, release notes, AppExchange
- Confirms, corrects, or upgrades recommendations with evidence links
- Discovers AppExchange alternatives reducing custom development scope
- Flags deprecated features or outdated assumptions
- Produces validation report with confidence ratings and source URLs

### Phase 5: Client Deliverables

**11. Client Elicitor** (`client-elicitor`)
- Consolidates **all open questions** from gap analysis, feature inventory, transcript analysis, and SFCC validation
- Deduplicates overlapping questions across sources
- Categorizes each question: Feature Clarification, Business Rule, Technical Feasibility, Data/Volume, Assumption Confirmation, Scope Decision, Platform Preference
- Prioritizes: P1 (must-answer before design), P2 (should-know before estimate), P3 (nice-to-know)
- Maps each question to stakeholder best positioned to answer
- Produces: Client-facing Q&A document + Meeting preparation guide with agenda

**12. Confluence Exporter** (`confluence-gap-analysis`)
- Converts markdown gap analysis to Confluence-ready output
- Produces Confluence Storage Format (XHTML) with status macros and structured tables
- Also produces Wiki Markup fallback for copy-paste into Confluence editor
- Matches standard Jira/Confluence gap analysis table format: Feature #, High-Level Functionality, Supporting Documentation, Current Site Feature, Decision (color badge), Notes
- Includes Decision Key, Summary statistics, Assumptions Register, and Open Questions tables

---

## Pipeline Options (A through H)

Each option represents a different entry point and execution path through the pipeline, optimized for different input types and engagement phases.

### Option A: Parallel Frame Analysis (Visual Deep Dive)

**Use case**: Running parallel frame analysis as a standalone operation; recommended first step for any new meeting recording.

**Input**: Video file with extracted frames and deduplicated manifest
**Output**: Screen Catalog, Component Library, System Architecture Map
**Execution**: Phase 1 parallel workload only

**Key features**:
- Spawns 5 frame-analyst agents in parallel, each processing ~42 frames
- Frame-synthesizer merges outputs into unified visual deliverables
- Produces raw visual inventory consumed by other agents downstream
- No business context yet (purely visual extraction)

**Timeline**: 2-4 hours depending on frame count

---

### Option B: Full Analysis Team

**Use case**: After parallel frame analysis completes (or run all at once for full end-to-end)

**Input**: Transcript file + Frame Synthesis outputs (Screen Catalog, Component Library, System Architecture Map)
**Output**: Feature Inventory, Gap Analysis
**Execution**: Phase 2 synthesis + Phase 3 analysis

**Key features**:
- 5 agents (meeting-analyst, sfcc-expert, ui-analyst, integration-analyst, gap-analyst) run with dependencies
- Meeting-analyst reads transcript + frame synthesis outputs
- UI-analyst consumes screen catalog and component library
- Integration-analyst reads system architecture map
- All feed to gap-analyst for final synthesis
- Plan approval required before gap-analyst writes final document

**Timeline**: 4-8 hours

---

### Option C: Combined (Frame Analysis + Full Team)

**Use case**: Single-command full run from frames through gap analysis

**Input**: Video frames directory (deduplicated)
**Output**: All Phase 1 + Phase 2 outputs
**Execution**: Phase 1 (parallel) → Phase 2 (full team)

**Key features**:
- Sequential phases: Phase 1 completes, then Phase 2 launches
- Automatic handoff of Frame Synthesis outputs to Phase 2 agents
- Full visual + business context in single run

**Timeline**: 6-12 hours

---

### Option D: Transcript-Only Analysis (Lightweight)

**Use case**: Fast path when you have only a text transcript (no video/frames); works with any transcript format

**Input**: Raw text transcript (Teams, Zoom, hand-typed, .vtt, .srt)
**Output**: Feature Inventory, Transcript Analysis Summary, Gap Analysis
**Execution**: Phase 1 analysis (transcript path) + Phase 2 synthesis + Phase 3

**Key features**:
- 4 agents (transcript-analyst, sfcc-expert, integration-analyst, gap-analyst)
- No frame processing — trades visual evidence for speed
- Transcript-analyst flags areas where visual review would add confidence
- Ideal for early-stage calls, quick follow-ups, or meetings without screen share

**Timeline**: 2-4 hours

---

### Option E: Transcript-Only → Confluence (End-to-End Lightweight)

**Use case**: Option D + immediate Confluence delivery

**Input**: Raw text transcript
**Output**: Gap Analysis + Confluence Storage Format + Wiki Markup
**Execution**: Phase 1-3 + Phase 5 (Confluence export only)

**Key features**:
- Extends Option D with confluence-exporter
- Confluence exporter depends on gap-analyst completion
- Produces Jira/Confluence-ready tables and macros

**Timeline**: 3-5 hours

---

### Option F: Full Pipeline from Raw Video (End-to-End)

**Use case**: New client engagement; drop a video file and get a Confluence gap analysis

**Input**: Raw video file (MP4, MOV, etc.)
**Output**: All preprocessing outputs + Phases 1-6 deliverables
**Execution**: Phase 0 (preprocessing) → Phase 1 (parallel frames) → Phase 2 (synthesis) → Phase 3 (gap analysis) → Phase 4 (validation) → Phase 5 (client deliverables) + Phase 6 (summary)

**Prerequisites**: `ffmpeg` installed, `ELEVENLABS_API_KEY` in `.env`, `uv` installed

**Key features**:
- Complete end-to-end automation from raw video
- Phase 0 sequential: extraction → dedup → transcription
- Phase 1 parallel: 5 frame analysts + synthesizer
- Phase 2-3 sequential with dependencies
- Phase 4-5 can run in parallel (validator and elicitor have limited cross-dependencies)
- Includes full validation and client preparation

**Timeline**: 12-20 hours (depending on video length, frame count, and external search time)

---

### Option G: Raw Video → Transcript-Only Analysis (Fast Triage)

**Use case**: Have a raw video but want fast turnaround without frame analysis

**Input**: Raw video file
**Output**: Frames (extracted but not analyzed) + Transcript + Gap Analysis
**Execution**: Phase 0 (preprocessing) → Phase 1 (transcript path only, no frame analysis) → Phase 2-3

**Key features**:
- Phase 0: Extract frames and transcribe (frames preserved for later if needed)
- Skips parallel frame analysis
- Runs transcript-only pipeline (Option D) after transcription
- Good for initial triage before committing to full visual analysis

**Timeline**: 4-8 hours

---

### Option H: Validation & Elicitation Only (Post-Analysis)

**Use case**: Already have a completed gap analysis; want to validate SFCC claims and prepare for next client meeting

**Input**: Existing gap analysis markdown file
**Output**: SFCC Validation Report + Client Elicitation + Meeting Prep Guide
**Execution**: Phase 4 + Phase 5 only

**Key features**:
- 2 agents (sfcc-validator, client-elicitor) run in parallel
- sfcc-validator searches Salesforce documentation for real-time fact-checking
- client-elicitor consolidates all questions from gap analysis and validation
- Fastest path to client follow-up preparation
- No re-analysis of original content

**Timeline**: 2-4 hours

---

## Input/Output Artifacts at Each Phase

### Phase 0: Preprocessing

**Inputs**:
- Raw video file (MP4, MOV, GIF, ffmpeg-supported format) OR
- Text transcript file (TXT, MD, VTT, SRT)

**Outputs**:
- `screencast/{meeting-name}-frames/manifest.json` — Frame and audio metadata
- `screencast/{meeting-name}-frames/frame_NNN.png` — Deduplicated video frames
- `screencast/{meeting-name}-frames/audio_NNN.aac` — Per-frame audio segments
- `screencast/{meeting-name}-frames/full_audio.aac` — Complete audio track
- `screencast/{meeting-name}-frames/audio-transcript.txt` — Diarized transcript
- `screencast/{meeting-name}-frames/dedup-report.json` — Deduplication statistics

---

### Phase 1: Parallel Analysis

**Inputs**:
- Deduplicated frames directory (manifest.json + PNG files)
- Full-length transcript (TXT or produced by Phase 0)

**Outputs** (if video source):
- `docs/frame-analysis-chunk-1.md` through `docs/frame-analysis-chunk-5.md` — Raw per-chunk frame inventories
- `docs/screen-catalog.md` — Deduplicated screen inventory
- `docs/component-library.md` — Unified UI component catalog
- `docs/system-architecture-map.md` — Navigation flows, ER sketches, field catalogs

**Outputs** (if transcript-only):
- `docs/feature-inventory-{company-slug}-{meeting-name}.md` — Feature inventories
- `docs/transcript-analysis-{company-slug}-{meeting-name}.md` — Cross-cutting concerns and follow-up questions

---

### Phase 2: Synthesis & Assessment

**Inputs**:
- Screen Catalog, Component Library, System Architecture Map (from Phase 1 video path) OR transcript outputs (Phase 1 transcript path)
- Full transcript (for context)

**Outputs**:
- `docs/feature-inventory-{company-slug}-{meeting-name}.md` — Comprehensive feature list
- `docs/ui-migration-map.md` — Component-to-LWC mapping
- `docs/integration-assessment.md` — Integration architecture and risks
- `docs/data-schema-mapping.md` — Entity-to-Salesforce-object mapping
- Internal team notes and assessments (may not be separate files; used by gap-analyst)

---

### Phase 3: Gap Analysis

**Inputs**:
- All Phase 2 assessment outputs
- Feature Inventory
- Transcript (for evidence and context)

**Outputs**:
- `docs/gap-analysis-{company-slug}-{meeting-name}.md` — Comprehensive gap analysis organized by client workflow
  - Feature-by-feature assessment
  - Gap severity, resolution options, effort estimates
  - Traceability to source meetings and business context
  - Assumptions Register and Open Questions tables

---

### Phase 4: Validation

**Inputs**:
- `docs/gap-analysis-{company-slug}-{meeting-name}.md`

**Outputs**:
- `docs/sfcc-validation-{company-slug}.md` — Validation report with confidence ratings and evidence links
  - Per-claim validation status (confirmed, corrected, flagged, alternative found)
  - AppExchange alternatives identified
  - Deprecated features flagged

---

### Phase 5: Client Deliverables

**Inputs**:
- Gap analysis (Phase 3)
- Validation report (Phase 4)
- Feature Inventory (Phase 2)
- Transcript Analysis (Phase 1)

**Outputs**:
- `docs/client-elicitation-{company-slug}.md` — Prioritized, stakeholder-mapped Q&A document
- `docs/meeting-prep-{company-slug}.md` — Meeting facilitation guide with agenda and talking points
- `docs/gap-analysis-confluence-{company-slug}.html` — Confluence Storage Format (paste into source editor or import via API)
- `docs/gap-analysis-confluence-{company-slug}.confluence` — Wiki Markup (paste into Insert → Markup → Confluence Wiki)

---

### Phase 6: Summary

**Inputs**:
- All preceding phase outputs and logs

**Outputs**:
- `docs/pipeline-summary-{company}-{date}.md` — Executive summary
  - Phases completed and elapsed time per phase
  - Documents generated (with file paths)
  - Key statistics: features found, gaps identified, validations performed
  - Confidence summary: high/medium/low confidence items count
  - Recommended next steps

---

## How the Pipeline Feeds into the Wiki

The migration analysis pipeline produces immutable artifacts stored in the client folder (e.g., `BostonBeerCompany/`). The wiki **consumes and elevates** these outputs through the ingest workflow.

### Pipeline → Wiki Flow

```
BostonBeerCompany/
├─ meetings/
│  ├─ transcripts/{date}.md (raw, immutable)
│  ├─ frames/ (raw frames and metadata, immutable)
│  └─ analysis/ (pipeline outputs: gap analysis, assessments, summaries)
         ↓
         [Wiki Ingest Workflow: New Meeting Transcript]
         ↓
wiki/clients/boston-beer-company/
├─ meetings/{YYYY-MM-DD}-{type}.md (synthesized summary)
├─ features/
│  ├─ budget-management.md (new or updated with meeting link)
│  ├─ dynamic-discount.md (new or updated)
│  └─ ...
├─ gaps/
│  ├─ dynamic-discount-gap.md (new or updated)
│  ├─ real-time-sync-gap.md (new or updated)
│  └─ ...
├─ decisions/
│  ├─ budget-solution.md (new or linked from gap)
│  └─ ...
└─ questions/
   ├─ can-sfcc-handle-10m-skus.md (new with priority and owner)
   └─ ...
```

### Ingest Workflow Steps

When a new pipeline output (gap analysis, feature inventory, validation report) is produced:

1. **Create or update meeting page** (`wiki/clients/{client}/meetings/{YYYY-MM-DD}-{type}.md`)
   - Synthesize key takeaways, attendees, action items
   - Link to raw transcript and analysis documents in sources
   - Link to features, gaps, questions discovered

2. **Extract and organize features** (or update existing)
   - For each business capability in Feature Inventory:
     - Create `wiki/clients/{client}/features/{feature-slug}.md` if new
     - Update feature page "Meeting History" section with link to new meeting
     - Link feature → meeting and feature → gaps

3. **Extract and organize gaps** (or update existing)
   - For each gap in gap analysis:
     - Create `wiki/clients/{client}/gaps/{gap-slug}.md` if new (status: `open`)
     - Update gap page with evidence links to pipeline analysis
     - Link gap → feature, gap → meeting, gap → decision (if one exists)

4. **Extract and organize questions**
   - For each open question in Client Elicitation output:
     - Create `wiki/clients/{client}/questions/{question-slug}.md` if new
     - Set priority (p0/p1/p2/p3), owner, and due date
     - Link question → feature, question → gap, question → decision

5. **Update wiki indexes** (`wiki/_index.md`, `wiki/clients/{client}/README.md`)
   - Register new pages in content catalog
   - Update client overview with metrics (features found, gaps, decisions, questions)

6. **Log activity** (`wiki/_log.md`)
   - Entry: `[{timestamp}] Meeting ingest: {client} — Discovered {N} features, {N} gaps, {N} questions; {M} pages created, {M} pages updated`

### Benefits of Pipeline → Wiki Integration

- **Immutability of raw outputs**: Pipeline produces unchangeable analysis documents; wiki references them
- **Traceability**: Every wiki page links back to pipeline source (gap analysis, feature inventory, transcript)
- **Cross-referencing**: Wiki enriches pipeline outputs by linking features to gaps to decisions to questions
- **Living artifact**: Gap analysis is consumed once; wiki synthesizes it into an evolving knowledge graph that grows with each meeting
- **LLM-friendly queries**: Wiki structure enables both human exploration and AI-powered pattern discovery

---

## Quality Gates and Validation Steps

The pipeline includes multiple quality gates to ensure confidence in outputs and catch errors early.

### Within-Pipeline Validation

**Frame Analyst Quality Check**:
- Each frame analyst produces a structured inventory with explicit component counts
- Frame Synthesis deduplicates and counts total unique screens
- Manifest discrepancies trigger alerts (e.g., frame count mismatch)

**Transcript Confidence Rating**:
- Transcript Analyst assigns confidence to each discovered feature: High/Medium/Low
- Low-confidence features are flagged for visual or stakeholder verification
- Summary report highlights features requiring follow-up

**SFCC Assessment Cross-Check**:
- SFCC B2B Expert independently assesses features against Salesforce documentation
- If assessment conflicts with earlier assessments, flagged for reconciliation
- Effort estimates are bracketed (e.g., "6-12 weeks") to reflect uncertainty

**Phase 2 Synthesis Review**:
- Gap Analysis agent reviews all Phase 2 outputs before finalizing
- Checks for:
  - Missing features (mentioned in transcript but not in assessment outputs)
  - Orphaned gaps (gaps without linked features or questions)
  - Effort estimate coherence (no huge jumps between related gaps)

**Plan Approval Gate** (Option C and beyond):
- Gap-analyst produces plan before writing final gap analysis
- Human or system approval required before continuing
- Catch scope issues, missing assessments, or contradictions early

### Post-Pipeline Validation (Phase 4)

**SFCC Validator**:
- Uses web search to validate every Salesforce claim in gap analysis
- Confirms OOTB features are still OOTB (not deprecated)
- Discovers AppExchange solutions reducing scope
- Produces validation report with evidence links (Salesforce docs, release notes, Trailhead)
- Flags claims that cannot be validated (prompts for escalation or research)

**Contradiction Detection**:
- Validator flags claims that contradict each other (e.g., "OOTB config" vs. "requires custom dev" for same feature)
- Highlights decision drift (e.g., "Use Vlocity" in Jan meeting, "Custom Apex" in March meeting without explicit decision)

### Wiki Lint Workflow

After pipeline output is ingested into wiki, periodic lint checks surface problems:

**Orphan Detection**: Features without gap pages; gaps without decision pages
**Stale Detection**: Features not updated since new meetings mentioned them
**Contradiction Detection**: Same feature assessed differently in different meetings
**Missing Cross-Refs**: Links expected but not found
**Overdue Questions**: P0 questions unanswered for > 2 weeks

Lint output is logged to `wiki/_schema/LINT_LOG.md` with recommendations for investigation and remediation.

---

## Key Design Decisions

### Parallel Frame Analysis
Video frames are chunked into 5 parallel workloads (~42 frames each per agent). This parallelization is reproducible, scales to longer meetings by adding chunks, and keeps agents within context limits.

### Client-Centric Gap Analysis
Gaps are organized by **client business workflow**, not exhaustive platform feature list. This makes deliverables more actionable and focused on what the client actually does.

### Iterative Meeting Processing
Each client meeting produces a Feature Inventory increment. The gap analysis evolves with each client interaction, becoming more complete and confident over time.

### Transcript-Only Path
Not every meeting has screen share or video. Transcript Analyst provides a lightweight entry point that works with any raw text, producing same Feature Inventory structure plus confidence ratings and follow-up questions.

### Post-Analysis Validation
Platform capabilities evolve. Validator uses real-time web search to fact-check claims, discover better options (AppExchange), and catch outdated assumptions.

### Assumptions-First Methodology
At analysis stage, explicit assumptions are logged rather than attempted to fully validate every detail. All assumptions are traceable in Assumptions Register within gap analysis, with impact-if-wrong and validation methods noted.
