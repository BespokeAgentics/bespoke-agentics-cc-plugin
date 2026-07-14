---
type: log
updated: 2026-07-13
---

# Wiki Operation Log

Chronological record of all bootstrap, maintenance, and schema evolution operations.

---

## 2026-07-13 — Plugin scaffold — Agent-Native Engineering suite (6 skills)

**Operation**: Added six skills + `/agentnative:{fast-ci,issue-to-agent,chore-crons,proof-of-work,hermetic-deploy,sim-data}` commands to the bespoke-agentics plugin.

**What it does**: Makes a codebase a good place for coding agents to work — the verification loop is the bottleneck, not generation. `fast-ci` swaps native tooling (TypeScript 7 GA, oxlint/oxfmt, uv, ruff; `TC*`/`LN*` catalogs) and splits fast pre-merge vs post-merge/merge-queue lanes; `issue-to-agent` dispatches claude-code-action v1 agents from triage labels (auto-triage, repro-on-label, PoC-on-label; injection-aware, zizmor-verified); `chore-crons` schedules agents onto the neglected tail (regression backfill, SDK gaps, skill tuning; single rolling channel, self-verification required); `proof-of-work` gives agents evidence tooling (agent-browser/Playwright capture, `evidence/` manifests, presigned-URL storage, PR evidence comments); `hermetic-deploy` builds one-command isolated instances (`H*` catalog, Compose `-p` namespacing, ephemeral ports, `dev-stack.sh` contract, N-instances verification); `sim-data` produces deterministic production-shaped seed scenarios (aggregate shape-mining, copycat/faker or Greenmask/anon with human-reviewed masking, double-seed determinism proofs).

**Files added**:
- `skills/fast-ci/` — SKILL.md + `references/{toolchain,pipeline-split}.md`
- `skills/issue-to-agent/` — SKILL.md + `references/workflows.md`
- `skills/chore-crons/` — SKILL.md + `references/cron-recipes.md`
- `skills/proof-of-work/` — SKILL.md + `references/{capture,storage}.md`
- `skills/hermetic-deploy/` — SKILL.md + `references/compose-isolation.md`
- `skills/sim-data/` — SKILL.md + `references/data-tools.md`
- `commands/agentnative/` — `fast-ci.md`, `issue-to-agent.md`, `chore-crons.md`, `proof-of-work.md`, `hermetic-deploy.md`, `sim-data.md`

**Registration**: `CLAUDE.md` (command table + suite paragraph + structure tree + getting-started 18–24), `.claude-plugin/plugin.json` and `marketplace.json` (description, keywords, version → 1.11.0; → 1.11.1 with the suite conductor).

**Addendum (same day)**: Added `commands/agentnative/suite.md` (`/agentnative:suite`) — a self-contained conductor command over the six skills: read-only readiness probe → 🟢/🟡/🔴 scorecard in `./plans/agentnative-suite.md` → one interview gate (dimensions, per-dimension mode, budget) → sequential Skill dispatch in dependency order (fast-ci → hermetic-deploy → sim-data → proof-of-work → issue-to-agent → chore-crons) with state persisted in `.agentnative/suite-state.json` (`--resume` skips landed work; a blocked dimension stops the chain).

**Facts basis**: Tool status (TS 7.0 GA 2026-07-08, oxfmt beta, ty beta-sidecar-only, Neosync archived, @snaplet/seed zombie, agent-browser/vercel-labs, claude-code-action v1 input model, Compose project-name precedence) verified against primary sources 2026-07-13; re-verify version-sensitive claims before relying on them downstream.

**Relationship to existing skills**: `fast-ci` complements `biome-guardrails` (lint policy) and `bun-workspace`; `issue-to-agent`/`chore-crons` are the event- and time-driven dispatch layers over the same guardrails as `orchestrate`; `proof-of-work` supplies the evidence conventions `orchestrate`'s smoke agent and `ux-audit` can consume; `hermetic-deploy` + `sim-data` form the runtime substrate the whole suite verifies against.

---

## 2026-05-30 — Plugin scaffold — progressive-disclosure skill

**Operation**: Added the `progressive-disclosure` skill + `/disclosure:{map,audit,refresh}` commands to the bespoke-agentics plugin.

**What it does**: Deploys parallel read-only subagents to profile every subsystem of a project/monorepo, then plans (dry-run, with diffs) and — on approval — writes a layered CLAUDE.md/AGENTS.md context hierarchy plus large-codebase config (Read deny rules, `additionalDirectories`, `claudeMdExcludes`, a SessionStart hook, code-intelligence recommendations). Implements the canonical "Set up Claude Code in a monorepo or large codebase" guidance. CLAUDE.md is the per-directory source of truth; AGENTS.md is a thin pointer. Idempotent via `progressive-disclosure:managed` sentinels. Reviews any `wiki/` for context and logs its own runs here.

**Files added**:
- `skills/progressive-disclosure/SKILL.md` (6-phase pipeline)
- `skills/progressive-disclosure/references/` — `large-codebases.md`, `settings-recipes.md`, `wiki-integration.md`
- `skills/progressive-disclosure/templates/` — `root-claude.md`, `subsystem-claude.md`, `agents-pointer.md`, `sessionstart-hook.sh`, `disclosure-plan.md`
- `commands/disclosure/` — `map.md`, `audit.md`, `refresh.md`

**Registration**: `CLAUDE.md` (command table + structure + getting-started), `.claude-plugin/plugin.json` and `marketplace.json` (description, keywords, version → 1.3.0).

**Relationship to existing skills**: Complements `architect-agents` (which builds the agent/command layer); this builds the context/memory layer. Defers deep wiki work to the `/wiki:*` commands.

---

## Lightweight Ingest — email — 2026-04-06

**Document**: Client email — MerchTank Feeder Systems (IT, Finance, Brand/Creative, Procurement)
**Company**: boston-beer-company
**Type**: email

**Classification**: Evidence + Clarification + Contradiction

**Pages Updated**:
- [[brand-budget-tracking|Brand Budget Tracking]]: Added Anaplan as budget source; contradiction notice vs Oracle assumption; new open questions about template format and LE cycles
- [[approval-workflows|Approval Workflows]]: Sam Central fully documented (no longer "unknown system"); approval threshold lookup confirmed as real-time
- [[buyer-user-management|Buyer User Management]]: Sam Central details added; cost center hierarchy documented
- [[buyer-account-model|Buyer Account Model]]: Cost center hierarchy from Sam Central noted as closest to account hierarchy
- [[custom-item-design-submission|Custom Item Design Submission]]: WorkFront, Adobe, Outlook, Vendor Portal workflows documented
- [[order-queue-and-fulfillment|Order Queue and Fulfillment]]: Vendor portal and Outlook quote workflows added
- [[product-catalog-and-browse|Product Catalog and Browse]]: WorkFront → MDM → SAP item setup workflow documented
- [[merchtank|MerchTank Entity]]: 5 new integration entries (Sam Central, Anaplan, WorkFront, MDM, SAP/SAP Ariba)
- [[oracle-erp|Oracle ERP Entity]]: Contradiction notice — budgets are in Anaplan, not Oracle
- [[oracle-erp-integration|Oracle ERP Integration]]: Contradiction notice — budget sync source is Anaplan, not Oracle
- [[vendor-fulfillment|Vendor Fulfillment Integration]]: Added vendor names (Kirkwood, Six Strings), Outlook quote workflow, SAP Ariba hard goods procurement
- [[oracle-erp-system-record|Q: Oracle ERP System Record]]: Partially answered — Anaplan is budget SOR; previous Oracle assumption marked as superseded
- [[budget-enforcement-behavior|Q: Budget Enforcement Behavior]]: Added Sam Central approval threshold evidence
- [[budget-management-engine|Gap: Budget Management Engine]]: Added Anaplan as budget source; updated Option 3 to target Anaplan

**Pages Created**:
- [[sam-central|Sam Central Entity]]: BBC's legacy coworker database — org hierarchy, approval thresholds, distributor mappings, cost center hierarchy
- [[anaplan|Anaplan Entity]]: BBC's financial reporting/planning system — source of truth for OPEX/brand budgets

**Contradictions Found**:
- **Budget Source (MAJOR)**: Wiki previously assumed Oracle ERP as budget system of record. Client confirms Anaplan is the budget SOR. "We do NOT maintain our budgets for OPEX in SAP, it lives here [Anaplan]." Affects oracle-erp entity, oracle-erp-integration, brand-budget-tracking, budget-management-engine gap, and oracle-erp-system-record question.

**Key Takeaway**: This email fundamentally changes the budget integration architecture by identifying Anaplan (not Oracle) as the budget source, and provides critical detail on Sam Central's role in access control and approval workflows. 7 feeder systems now documented: Sam Central, Anaplan, WorkFront, Adobe Creative Suite, Outlook, Vendor Portals, MDM/SAP/SAP Ariba.

**Status**: ✓ Complete

---

## 2026-04-06 — Initial Wiki Bootstrap

**Operation Type:** Full wiki bootstrap from analysis pipeline outputs

**Scope:** All Boston Beer Company client intelligence, 5 customer meetings, 3 gap analysis batches, platform knowledge base, integration assessments

**Pages Created:** 51 (plus 3 platform pages + 1 index infrastructure file = 55 total)

### Sources Ingested

**Meeting Analysis Pipeline:**
- `BostonBeerCompany/meetings/01-merchtank-overview/` (Partial — early frame analysis only)
  - gap-analysis-sample-bbc-merchtank.md
  - bbc-system-architecture-map.md

- `BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/` (Full pipeline)
  - gap-analysis-bbc-vw-walkthrough.md
  - integration-assessment-vw-walkthrough.md
  - Confluence exports

- `BostonBeerCompany/meetings/03-custom-requests/` (Full pipeline + validation)
  - gap-analysis-bbc-custom-requests-meeting.md
  - client-elicitation-bbc.md
  - integration-assessment-custom-requests-meeting.md
  - Confluence exports

- `BostonBeerCompany/meetings/04-fulfillment-demo/` (Full pipeline + validation)
  - gap-analysis-boston-beer-company-fulfillment-demo.md
  - client-elicitation-boston-beer-company.md
  - integration-assessment-fulfillment-demo.md
  - feature-inventory-boston-beer-company-fulfillment-demo.md
  - Confluence exports

- `BostonBeerCompany/meetings/05-finance-workflow/` (Stub — unprocessed)
  - No analysis outputs yet; requires pipeline run

**Gap Analysis Batches:**
- `BostonBeerCompany/gap-analysis-batch-3-my-account.md` — Account structure, user management, address book

**Platform Knowledge:**
- `salesforce/salesforce-commerce-product-configuration-guide/` — Config guide, bootstrap kit
- `salesforce/sf-commerce-bootstrap-kit/` — 01_bootstrap_runbook.md
- `Lightning-web-runtime-docs/` — 10 architecture documents covering LWR, B2B Commerce APIs, custom components
- `BostonBeerCompany/CLAUDE.md` — Client profile and system context

### Pages Created by Type

**Features (20):**
1. address-book-management
2. approval-workflows
3. brand-budget-tracking
4. buyer-account-model
5. buyer-user-management
6. co-op-billing
7. custom-item-design-submission
8. digital-file-delivery
9. order-history-and-analytics
10. order-queue-and-fulfillment
11. pack-based-ordering-model
12. product-catalog-and-browse
13. program-based-ordering-windows
14. proxy-ordering
15. rootstock-eap-integration
16. shipment-recording
17. shopping-cart-with-budget
18. virtual-warehouse-model
19. virtual-warehouse-transfers

Note: 18 custom features, 1 config feature (product-catalog-and-browse)

**Gaps (10):**
1. budget-management-engine (Critical)
2. co-op-billing (Critical)
3. custom-item-design-and-proofing (Critical)
4. procurement-controlled-order-release (High)
5. program-window-time-gating (High)
6. proxy-delegate-ordering (High)
7. request-access-flow (High)
8. self-registration-with-dual-auth (Medium)
9. virtual-warehouse-inventory-model (Critical)
10. virtual-warehouse-inventory-transfers (High)

**Meetings (5):**
1. 01-merchtank-overview (2025-12-04) — Status: Partial
2. 02-virtual-warehouse-walkthrough (2026-02-02) — Status: Complete
3. 03-custom-requests (2026-03-01) — Status: Complete
4. 04-fulfillment-demo (2026-03-15) — Status: Complete
5. 05-finance-workflow (2025-12-09) — Status: Unprocessed

**Questions (5):**
1. budget-enforcement-behavior (P1)
2. oracle-erp-system-record (P1)
3. salesforce-order-management-licensing (P1)
4. upstream-batch-system-identity (P1)
5. virtual-warehouse-active-usage (P2)

**Entities (4):**
1. boston-beer-company (Organization)
2. merchtank (System, Legacy)
3. oracle-erp (System, External)
4. tradewearables (Vendor)

**Integrations (4):**
1. oracle-erp-integration (Bidirectional, Batch, Planned)
2. sso-authentication (Bidirectional, Real-time, Planned)
3. tradewearables-api (Inbound, Batch, Planned)
4. vendor-fulfillment (Outbound, On-demand, Planned)

**Platforms (3):**
1. salesforce-b2b-commerce/overview
2. salesforce-lwc/overview
3. merchtank/overview

### Known Coverage Gaps (Flagged for Lint)

- **Meeting 05 (Finance Workflow)** — Unprocessed. Stub page exists but no analysis pipeline outputs. Requires full transcription, video frame analysis, gap extraction, and elicitation synthesis. **Blocker:** Finance team participation creates budget-related questions across other meetings; this meeting would clarify upstream finance system constraints.

- **Meeting 01 (MerchTank Overview)** — Partial analysis only. Early-frame analysis completed but full video transcription + gap extraction incomplete. This meeting provides foundational context for MerchTank system design. **Recommendation:** Re-run full pipeline to capture all gaps.

- **Decision Pages** — Not yet created. Decisions are currently embedded in feature and gap pages. A dedicated decision record (ADR-style) for each major design choice would improve traceability. **Candidates:** Budget enforcement approach, virtual warehouse allocation model, co-op billing calculation, SSO strategy.

- **Question Coverage** — Limited to P1/P2 from elicitation documents. P3 and exploratory questions (design trade-offs, vendor constraints, roadmap trade-offs) not yet extracted. **Note:** Questions capture "blocking" and "confirmatory" unknowns; design questions are captured as gaps.

### Structure Validation

- **Wiki conventions:** All pages follow SCHEMA.md frontmatter standards (type, client, status, category, created/updated dates, source links, tags)
- **Cross-references:** Feature-to-gap links present; gap-to-meeting source references complete
- **Naming:** Consistent kebab-case slugs; titles follow convention
- **Tagging:** Consistent tag vocabulary across 20+ feature/gap tags
- **Status values:** Features (draft), Gaps (open), Meetings (partial/complete/unprocessed), Integrations (planned), Questions (open)

### Next Steps

1. **Meeting 05 pipeline run** — Unprocessed Finance meeting requires transcription, analysis, and gap/question extraction
2. **Meeting 01 re-analysis** — Complete full pipeline for MerchTank overview (currently partial)
3. **Decision record creation** — Convert major design decisions into ADR-style decision pages
4. **Question extraction** — Expand question coverage to P3 and exploratory unknowns
5. **Lint validation** — Run schema linter against all pages to verify frontmatter consistency
6. **Link validation** — Verify all [[wiki-links]] resolve correctly

---

