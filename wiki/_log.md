---
type: log
updated: 2026-09-17
---

# Wiki Operation Log

Chronological record of all bootstrap, maintenance, and schema evolution operations.

---

## 2026-08-19 — Command surface de-duplication — 18 wrapper commands folded into their skills

**Trigger**: the Claude Code `/` picker showed each capability multiple times, e.g.
`/bespoke-agentics:bespokeagentics:dead-code-sweep` next to
`/bespoke-agentics:dead-code-sweep`.

**Root cause, two independent defects.**

1. **Namespace stutter.** 29 root commands and 5 `SKILL.md` files declared
   `name: "bespokeagentics:<leaf>"`. Claude Code already prefixes the plugin
   name, so the published form was `/bespoke-agentics:bespokeagentics:<leaf>`.
   The rule that produced this was written down in
   `skills/setup-plugin/references/plugin-structure.md` ("Full name:
   `bespoke-agentics` → `bespokeagentics:`") and in `setup-plugin/SKILL.md`,
   so every new command inherited it.
2. **Double publication.** 18 capabilities shipped as BOTH a skill and a thin
   wrapper command whose body restated the skill and delegated to it. Two
   registries, two picker rows, one capability.

**Changes.**

- Stripped the bogus prefix from all 29 command `name:` fields and all 5
  `SKILL.md` `name:` fields. Names now equal the filename / directory.
- Folded the 18 wrapper commands into their skills and deleted them. Each fold
  ported only the genuinely unique artifact — the argument/flag contract — into
  the skill body; process and output sections were dropped as restatements.
  Commands dropped from 67 to 49.
- Rewrote 104 `/bespokeagentics:` references across 23 files to
  `/bespoke-agentics:`, plus eval prompts in three `evals.json` files,
  `scripts/ai-transparency-check.sh`, and the xstate migration-plan template.
- Corrected the guidance that caused it: the naming table now says a command
  `name` is kebab-case matching the filename, and a new **Namespace Selection**
  section states that the namespace names the _group_ (`wiki:query`,
  `bun:add`), never the plugin. Added a **Commands vs. skills: do not ship
  both** rule.
- Updated the `commands/` tree in `CLAUDE.md`, which listed 13 files that no
  longer exist.

**Collateral defect found and fixed.** `apps/spec-interviewer` read
`commands/spec-elicitation.md` at runtime (`server/interview.ts`, two
`fs.readFile` call sites). Deleting that command would have hard-broken the app
with ENOENT. Repointed to `skills/spec-elicitation/SKILL.md`, along with the
matching claims in `README.md`, `apps/spec-interviewer/README.md`, and that
app's `package.json` description.

**Known loss**: `commands/spec-elicitation.md` carried `model: opus`. No
`SKILL.md` in this plugin uses a `model:` field, so that pin did not survive the
fold. `apps/spec-interviewer` still defaults to `opus` independently.

**Not done**: version not bumped and nothing committed. The removal of 18
commands is breaking for anyone who types them; the `bump-version.sh` pre-commit
hook only bumps PATCH.

---

## 2026-07-27 — Skill audit — skill-reverse-engineer run against data-ui-craft

**Operation**: `/bespoke-agentics:skill-reverse-engineer skills/data-ui-craft --mode audit` — read-only determinism audit. Nothing in the target was modified.

**Verdict**: 🟡 improvisation-dependent. Of 20 reconstructed steps, **0 are owned by a bundled artifact and 12 are mechanical work the model re-derives every run**. The judgment layer is strong (stable-ID `DF*`/`PD*`/`IU*` rule catalog with detection cues + default severities, an explicit calibration section, 15 real `.tmpl` files, a literal markdown report template, 0 ALL-CAPS directives, correct progressive disclosure, a properly gated destructive step); the mechanical layer does not exist — `skills/data-ui-craft/` has no `scripts/` directory.

**Findings**: 0 CRITICAL · 4 HIGH · 5 MEDIUM · 3 LOW.

- **H1 (DS1)** stack detection + surface discovery as prose (`SKILL.md:77-109`) — the audit's _scope_ varies run to run → `detect_stack.py`, `find_surfaces.py`
- **H2 (DS4)** `templates/index.ts.tmpl:5-21` exports 13 modules a partial scaffold won't have written, against "write only the primitives that are actually needed" (`SKILL.md:168`) → `scaffold_kit.py` generating the barrel from the selected set
- **H3 (TP2)** 118-line HTML report skeleton retyped every run (`references/report-format.md:72-189`) → `assets/audit-report.html` + `render_report.py`
- **H4 (CT1)** findings never leave context — counts tallied by the model, md/html written independently, `implement` re-scans by design (`SKILL.md:153-154`) → `./data-ui-craft-audit.json` + `assets/rules.json`
- **M1 (KM4)** cross-stack adapter mapping stated 11× and already divergent · **M2 (AM3)** `{{CN}}` contract contradicts itself across 3 files · **M3 (VF1)** layout sanity pass = 5 decidable conditions, no check, optional trigger · **M4 (AM2)** no degradation section for tsc/linter/browser · **M5 (CT3)** no argument grammar · **L1 (KM5)** severity palette is an uncited copy of `ux-audit`'s (verified identical today, no drift check) · **L2 (RB2)** two instructions cite an authoring-time conversation no run can see · **L3 (RB5)** fixed root-level report paths silently overwrite the prior audit

**Essential-judgment register** (8 entries — the AI-reliance that must stay): applying detection patterns as _proxies_, severity calibration, data-type inference from column defs, respecting deliberate product choices, frequency × importance placement, PM-facing prose, in-place fix application, Opportunity selection.

**Host state**: `no-host` — the cwd is the plugin repo that authors the skill, not a data-dense app it operates on, so KM1–KM3 were not gradeable; both candidate host facts failed the materialization test on their own merits regardless (stack = recomputable in <1s → runtime script; surfaces = volatile working state → anti-list).

**Files added**:

- `reviews/skill-re-data-ui-craft.md` — the read-only report
- `reviews/skill-re-data-ui-craft.host-context.json` — host-state sidecar + `knowledge_sources` worklist

**Corrections made during the run**: `inventory.py` reported 1 broken internal reference — verified false positive (its `REF_PATH` regex truncates `templates/README.md.tmpl` at `.md`; the file exists). The target has 0 broken references. Logged as a defect in the _auditing_ skill, out of scope for this run.

**Not executed**: the 13 `.tsx.tmpl` files were reviewed statically — no React/TypeScript toolchain was exercised, so H2's barrel mismatch is a reading of the template against `SKILL.md:168`, not an observed `tsc` failure.

---

## 2026-07-22 — New skill + command — wireframe-parity (v1.20.0)

**Operation**: Added the `wireframe-parity` skill + `/bespoke-agentics:wireframe-parity` command — a read-only reviewer that confirms an implemented UI matches the wireframe an `interactive-wireframe` spec settled.

**What it does**: The post-implementation companion to `interactive-wireframe`. It does not invent the "intended" side — the wireframe already froze it: the spec's **Verification** table is a snapshot of `__wf` measurements (band contiguity, contrast + AA/AAA, `button button` count, off-screen focusables), **The contract** holds structural invariants + numbers, the **Decisions** table + `_library/decisions.md` ledger record what was settled, and the **States** table is the overlay's axes resolved (each row reproducible as a wireframe URL). Two passes: **(1) structural** — parallel `Explore` agents ground every settled decision/state/label in the real implementation (`file:line`), honored/drifted/missing (the `--no-browser` floor); **(2) measured** — serves the wireframe (reusing `interactive-wireframe`'s `scripts/serve-wireframe.sh`) and injects the **same** dependency-free probe (`assets/wf-probe.js`, a standalone copy of the scaffold's `__wf` kit + two parity extras `texts()`/`token()`) into **both** the wireframe and the running app via claude-in-chrome, drives each to the matching state, and diffs band geometry / contrast / markup / focusables / labels / tokens apples-to-apples. Parity is invariant-**within-tolerance** (±2px geometry, same AA/AAA verdict, contiguity as the contract requires), never pixel-identity (user declined strict). Auth-gated states are labelled "not measured", never assumed; a backgrounded-tab behavioural "failure" is a measurement artifact. Because **spec Decisions are the parity contract** and a build sometimes evolves past the wireframe on purpose, an AskUserQuestion interview classifies each divergence as **regression** / **intended-evolution** / **out-of-scope** before any is called a failure; `--depth deep` adversarially verifies each first. Writes a read-only `./reviews/<slug>-parity.md` (verdict 🟢/🟡/🔴, decision-by-decision parity table, measured table intended/spec-frozen/as-built/Δ, label fidelity, color-coded divergence register, honest "not measured" coverage, definition-of-parity checklist), offers (doesn't assume) to open P0 regressions as tasks or refresh the stale ledger, and wiki-ingests + logs when a vault exists.

**Files added**:

- `skills/wireframe-parity/SKILL.md` (6-phase pipeline, cloned from the plan-review reviewer scaffold)
- `skills/wireframe-parity/references/` — `resolve-and-parse.md`, `grounding.md`, `measurement.md`, `interview.md`, `report-synthesis.md`
- `skills/wireframe-parity/assets/wf-probe.js` — the injectable measurement kit
- `skills/wireframe-parity/assets/templates/` — `parity-report.md`, `divergence-register.md`, `finding.schema.json`
- `commands/wireframe-parity.md`

**Files modified**:

- `skills/interactive-wireframe/SKILL.md` + `references/spec-template.md` — cross-links noting the Verification table + Decisions are what wireframe-parity re-measures post-implementation

**Design/reuse basis**: mirrors `plan-review`'s scaffold (thin command → phased skill with per-phase references, parallel `Explore` grounding to `file:line`, `--depth deep` adversarial verification, AskUserQuestion gate, `./reviews/` output with 🟢/🟡/🔴 + color-coded register + wiki ingestion), fused with `interactive-wireframe`'s in-page `__wf` assertions and `funcspec`'s code-said-X-render-shows-Y contradiction check. `wf-probe.js` is a faithful copy of the scaffold `__wf` methods (geometry/contrast/markup/focusables/behaviour) injected into both sides so the diff is drift-proof; a `methods()` self-report supports the drift check.

**Verification**: wf-probe.js injected into a served scaffold via claude-in-chrome returned `bands`/`contrast`/`markup`/`texts`/`token` shapes matching the built-in `__wf`; JS + JSON syntax checks pass; command/skill flag sets agree; version strings agree across plugin.json/marketplace.json.

**Registration**: `CLAUDE.md` (new "When to Use the Wireframe-Parity Command" section + paragraph, Getting Started item 29, structure tree skills/ + commands/), `.claude-plugin/plugin.json` and `marketplace.json` (keywords `wireframe-parity`/`design-parity`/`as-built-review`/`visual-parity`/`ui-parity`, version → 1.20.0).

**Relationship to existing skills**: post-implementation companion to `interactive-wireframe` (consumes its spec + wireframe + `_library/decisions.md`); distinct from `plan-review` (audits a document _before_ build) and `ux-audit` (heuristics on a UI) — this audits a _built UI against the wireframe that specified it_.

---

## 2026-07-22 — Skill upgrade — interactive-wireframe 2-way browser feedback (v1.19.0)

**Operation**: Added a two-way browser↔session communication path to the `interactive-wireframe` skill: an in-page comment mode (element picking + free-page comments + reply thread panel), a file-based transport through the serve script, and an optional Claude Code **channel** server for instant push.

**What it does**: While a served wireframe is open in the browser, the user enters comment mode (✎ button or `c`), picks any element (hover-highlight, click — the click is swallowed, never triggering the underlying control), and comments; the payload carries the derived CSS selector, nearest `data-z` zone, nearest `▼ FRAGMENT` name, text snippet, bounding rect, the full axis state `WF.S`, and the URL hash — pinning exactly what was on screen. Transport is layered: the page POSTs same-origin to the serve script's new `POST /__feedback` (loopback-only, ≤64KB, JSON-validated) → `<slug>/.feedback.jsonl`; agent replies (via the new `reply` subcommand or the channel's `reply` tool) append `<slug>/.replies.jsonl`, which the page polls (~2s, backoff) into a thread panel with sent/queued/replied statuses; the thread survives rebuild-between-rounds reloads via one-shot reconstruction. **Layer 1** (every session): `feedback` (cursor-based drain, exit 0/1), `await-feedback` (blocking, exit 0/124 — run as a background Bash task that wakes the agent), `reply --to <fb-id>`; `start` auto-replaces live pre-v2 servers (`"v":2` state marker). **Layer 2** (optional, research preview): `channels/wireframe-feedback/server.ts` — an MCP channel (`capabilities.experimental['claude/channel']`) that watches the same files and pushes each comment into the running session as a `<channel>` event (meta `fb_id/slug/kind`), plus a `reply` tool; registered via the target project's `.mcp.json` (offered once), launched with `claude --dangerously-load-development-channels server:wireframe-feedback`; liveness is probed by the reply tool's visibility (channel live → never also poll, preventing double delivery). Degrades gracefully: no endpoint/`file://` → clipboard-copy fallback with a visible hint. Comment text is framed as end-user feedback to triage (change → rebuild, question → reply, approval → decision row), never as instructions. Also fixed a latent serve-script bug: `port_holder` could abort the port scan under `set -euo pipefail` when a port was in TIME_WAIT (busy to bind, invisible to lsof), and `port_free` now probes with SO_REUSEADDR to mirror the server's own bind.

**Files added**:

- `channels/wireframe-feedback/server.ts` + `package.json` — the channel server (Bun + @modelcontextprotocol/sdk)
- `skills/interactive-wireframe/references/live-feedback.md` — schemas, subcommand contracts, channel setup, triage protocol, degradation matrix, security gate

**Files modified**:

- `skills/interactive-wireframe/scripts/serve-wireframe.sh` — `do_POST`, `"v":2` + auto-relaunch, `feedback`/`await-feedback`/`reply`, port-helper fixes
- `skills/interactive-wireframe/assets/wireframe-scaffold.html` — feedback kit (`__wfFb` harness IIFE + `.wf-fb-*` chrome; `__wfFb.comment()` programmatic test hook)
- `skills/interactive-wireframe/SKILL.md` — Phase 3 endpoint + channel offer + liveness rule, Phase 4 browser-comments bullet, artifacts/gitignore, reference table
- `skills/interactive-wireframe/references/{interview,browser-verification}.md` — "Browser comments during rounds" subsection; feedback-path checklist line
- `commands/interactive-wireframe.md` — process steps 4/5 + Output (no new flags)

**Verification**: transport curl matrix (204/400/404/413), cursor semantics, blocking await woken by a parallel POST, threaded reply rendered in-page ≤2.5s with status flip, reload reconstruction, click-swallow while picking, clipboard fallback, and a full stdio JSON-RPC smoke test of the channel (capability + instructions, no history replay, exactly one notification per new entry with correct meta, reply tool write, traversal-slug rejection).

**Registration**: `CLAUDE.md` (command paragraph, getting-started 28, structure tree + `channels/`), `.claude-plugin/plugin.json` and `marketplace.json` (keywords `live-feedback`/`browser-comments`/`feedback-channel`/`claude-channel`, version → 1.19.0).

---

## 2026-07-22 — Skill upgrade — interactive-wireframe cross-run reuse library (v1.18.0)

**Operation**: Added a per-project reuse mechanism to the `interactive-wireframe` skill — grounding cache, fragment library, and decisions ledger under `<out>/_library/` + `<out>/_index.md`, consumed at grounding/build/interview time and auto-harvested at spec emission.

**What it does**: Repeat wireframe runs in the same project start warm instead of re-deriving everything. Motivating evidence (CUMULATIVE*OS, 2 real runs): byte-identical token tables across both runs' `grounding.md` (the second hand-wrote "reused verbatim — see <other-slug>"), ~17% of each wireframe file being project chrome rebuilt from scratch, and settled decisions (`structure: flat`, `railW: 236`) carried between runs by hand. Three layers: **grounding cache** (`_library/grounding-cache.md`, per-section `verified` dates, TTL-trusted — default 14 days, `--ttl <days>` — with the three honest label states `cached — verified` / `cached — re-verified` / re-derived-on-drift; drift is a Gaps finding); **fragment library** (`_library/fragments/*.{html,css}`, self-describing headers with origin/sources/token-deps/feeds, injected into the scaffold's REPLACE regions wrapped in `▼ FRAGMENT … ▲ /FRAGMENT` markers so harvest is a mechanical diff); **decisions ledger** (`_library/decisions.md`, append-only, reopened rows marked superseded; verdicts imported into round 1 as fixed context with one "reopen?" affordance, landing in specs as `Settled by: carried (<slug>/Dn)`). Harvest runs automatically at Phase 6 (settled-context heuristic, cap 5 fragments; even under `--fresh`, which skips only consumption); projects with prior runs but no library get a one-time backfill offer (backfilled entries earn `verified:` only after their `path:line` anchors pass a grep). Library is per-out-dir — tokens never transfer between products; slugs must not start with `*`.

**Files added**:

- `skills/interactive-wireframe/references/reuse-library.md` — the single source of truth (layout, three layers, TTL rules, per-phase consumption, harvest algorithm, backfill, honesty rules)

**Files modified**:

- `skills/interactive-wireframe/SKILL.md` — Phase 1 cache-first check, Phase 2 fragment injection, Phase 4 ledger bullet, Phase 6 harvest step, Artifacts tree (`_index.md` + `_library/`), reference-files table row
- `skills/interactive-wireframe/references/{grounding,interview,spec-template}.md` — cache-first pointer + cached-label heading form; "Consuming the decisions ledger" subsection; `carried (<slug>/Dn)` legend
- `skills/interactive-wireframe/assets/wireframe-scaffold.html` — banner note on seeding regions 1–3 from fragments (harness untouched)
- `commands/interactive-wireframe.md` — `--fresh` / `--ttl <days>` flags, process steps 2/3/5/7, output section

**Registration**: `CLAUDE.md` (command-table flags + command paragraph + getting-started 28), `.claude-plugin/plugin.json` and `marketplace.json` (keywords `wireframe-reuse`/`fragment-library`/`decisions-ledger`, version → 1.18.0).

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

## 2026-09-16 — project-db skill added — queryable database over the wiki (v2.7.0)

**What**: new skill `skills/project-db/` + commands `/db:init`, `/db:query`, `/db:sync`, `/db:publish`.
Builds a SQLite index of the wiki (pages, frontmatter fields, wikilinks with resolution, tags, sources,
sections, cited raw documents, FTS5), one typed view per page type with column docs mined from
`_schema/templates/`, curated cross-type views, a guarded read-only query CLI, a SessionStart sync
hook, a local MCP server, and a Cloudflare D1 + Worker publish path. Without a wiki: interview +
codebase scan → schema → DB-first mandate.

**Why**: agents answered structured questions ("which critical gaps…", "which meetings mentioned…")
by reading pages one by one. SQL over the wiki answers them in one query; the wiki stays the record,
the database is the index (derived, gitignored, rebuilt incrementally).

**Verification**: engine tested on this vault (61 pages, 745 links, 30/30 verify checks), on a
no-wiki fixture (typed views + CSV/JSON tables), on local D1 (FTS5, views, JSON), and over MCP stdio.
Evals in `skills/project-db/evals/`.

## 2026-09-17 — project-ontology skill added — enforceable dot-notated vocabulary (v2.8.0)

**What**: new skill `skills/project-ontology/` + commands `/ontology:init`, `/ontology:check`,
`/ontology:propose`, `/ontology:approve`, `/ontology:deprecate`, `/ontology:apply`, `/ontology:status`.
`init` mines a vault (page types, template `key: # a|b|c` vocabularies, SCHEMA.md value lists, observed
values, scope folders, tags, frontmatter link fields) into `wiki/_schema/ontology.yaml` — dot-notated terms
with a proposed → approved → deprecated lifecycle — rendered to `ONTOLOGY.md`. One stdlib engine enforces it:
PreToolUse ratchet hook (blocks writes that add strict violations; pre-existing ones never block), PostToolUse
context, Bash guard (approvals → permission prompt; shell writes into pages blocked), SessionStart banner,
`check --changed-since` for CI. project-db (engine 1.1.0, schema v2) loads `ontology_terms`,
`ontology_aliases`, `ontology_fields`, `ontology_violations` and `pages.ontology_id`; wiki-lint gains Check 8
and Check 6 now reads the vault's vocabulary instead of a hard-coded list; wiki-init, wiki-ingest-meeting,
wiki-ingest-document and knowledge-loop use registered values.

**Why**: this vault's vocabulary had drifted in four places — SCHEMA.md, the page templates, wiki-lint's
hard-coded checks and ingest-meeting's defaults disagreed (e.g. gap status `open|under-review|resolved|workaround`
vs `open|mitigated|resolved|accepted`); `client` was written `Boston Beer Company` on 10 pages and
`boston-beer-company` on 40; all 19 features carry `status: draft`, which no vocabulary declares.

**Decisions** (design interview): plain values with path-derived ids; strict ratchet; wiki + DB + agent
context; separate skill with a PreToolUse hook; global vocabularies, path-scoped ids; human-only approval.
See `docs/plans/project-ontology.md`.

**Verification** (scratch copy of this vault, defaults, no page edited): 241 terms (93 approved, 148
proposed), every observed value classified (51 approved · 147 proposed · 1 noncanonical · 0 unknown); 698
open violations (445 strict — 288 broken links, 130 noncanonical links, 10 relation-broken, 10 client
variants, 7 ambiguous links; 253 warn), none blocking; `apply --dry-run` = 140 mechanical rewrites in 31
files; a Write adding `severity: urgent` is blocked naming `critical · high · medium · low`. Engine tests
59/59, project-db tests 23/23. Evals (3 × with/without skill, graded by re-running each run's installed hooks):
with skill 29/29, baseline 25/29 — the baseline misses were governance (unrequested page rewrites, no
SessionStart surfacing, unlogged lint run). The live vault was not modified: installing enforcement here is a
separate decision.

**Defects fixed along the way**: project-db parsed frontmatter with PyYAML when installed (`related: [[Page]]`
lost its link on those machines) and dropped unindented YAML block lists; links inside code blocks counted as
links; wiki-lint Check 6 hard-coded a vocabulary that contradicted the vault; ingest-meeting wrote
`status: identified`, a value this vault does not declare.
