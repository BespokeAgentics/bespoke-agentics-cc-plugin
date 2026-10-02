# Prompt audit — bespoke-agentics-cc-plugin

- **Date**: 2026-09-28
- **Method**: `/claude-api prompt-audit` (Anthropic prompt-audit guide, Steps 0–6). Read-only; edits proposed as patches only.
- **Patches**: `reviews/prompt-audit-2026-09-28-patches/` — one `git apply`-able patch per batch (see § Proposed diff).
- **Status**: all 8 patches **applied** to the working tree on 2026-09-28 (uncommitted), with 3 regression guards added and all 9 gates green. See § Applied and verified.

## Assumptions (Step 0)

| | |
|---|---|
| **Scope** | Whole working-directory prompt surface on branch `feat/plugin-context-reduction`, **including its ~140 uncommitted modifications**: root `CLAUDE.md`, `OPERATING-MANUAL.md`, `CLAUDE.wiki.md`, `README.md` (conflicts only), `agents/` (10), `commands/` (60), `skills/` (74 skills: SKILL.md, references, templates, injected hook/mandate text), `hooks/hooks.json`, `channels/wireframe-feedback/`, `install-tts-hook.sh`. |
| **Skipped** | `evals/`, `*-workspace/`, `fixtures/`, `wiki/`, `docs/`, `reviews/`; `.claude/settings*.json`, `.mcp.json` (may hold secrets); `~/.claude/CLAUDE.md` (user-level, outside project — conflicts only flagged). |
| **Target model** | Claude Opus 5.5 (the model running the audit; coding-agent config). `agents/{workflow-analyzer,video-to-deliverables,ai-transparency}.md` pin `model: sonnet` → Claude Sonnet 5. `install-tts-hook.sh` summarizer → Claude Haiku 4.5 (cheap, latency-bound). |
| **Non-Anthropic markers** | `skills/session-hooks/templates/start-ai-consultation.py` (OpenAI/Gemini branches), `skills/glean-agent-toolkit/templates/*` (OpenAI/Gemini), `skills/codex-prompt-builder` (Codex target). Only Anthropic branches audited; no provider switches proposed. |
| **Plugin context** | Every skill/command is `disable-model-invocation: true`, so frontmatter `description`s are not model context and were not audited as routing text. |

## Summary

Group 1 (dated prompt text) is **nearly clean**: almost every MUST/NEVER guards a real gate (approval before edit, credentials, deletion, commits), which the keep list protects. The rot is in **Group 2 — stale facts and files that contradict each other**. The three highest-impact problems:

1. **Wrong API facts shipped as audit rules and fix code.** `agent-loop-audit` greps for `session.status.idle` (real: `session.status_idle`), reads `stop_reason.kind` / `"completed"` (real: `stop_reason.type` ∈ `end_turn|requires_action|budget_reached` + `event_ids`), counts five input events (six), and prescribes a non-existent `client.sessions.connect()`. `ai-waiting-ux` inverts `end_turn`/`tool_use` and assumes thinking is off by default. The skills built to catch silent hangs would themselves produce code that hangs. *(verified against the bundled Managed Agents docs)*
2. **Hook `timeout` written in milliseconds; Claude Code reads seconds.** `hooks/hooks.json:10` (`10000` → ~2.8 h, this repo's own live hook), `setup-plugin` (teaches `10000` to every generated plugin), `biome-guardrails` (`5000`/`15000`).
3. **Manual-only migration left dangling references.** After the branch made every skill manual-only, ~20 places still say "invoke the X skill" / "use the Skill tool" / name renamed skills (`new-micro`, `verify`, `deploy`), use repo-root-relative `skills/...` paths that don't resolve in a user's project, or promise "implicit" invocation. `README.md:19` still says skills trigger automatically.

Also notable: `install-tts-hook.sh:114` defaults to retired `claude-3-5-haiku-latest` (every Anthropic summarizer call fails silently); `/wiki:lint --fix` never fixes (skill's `report-only` defaults true); a client-specific `wiki/verndale/playbooks/` path is written into every user's vault; root `CLAUDE.md` is ~135 KB (~34K tokens, every session) with its skill descriptions restated twice and already drifting.

### Counts

| Group | Findings | High | Medium | Low / flag |
|---|---|---|---|---|
| 1 — Dated prompt text | 17 | 0 | 9 | 8 |
| 2 — Brittle skill/config files | 102 | 38 | 38 | 26 |
| 3 — Tool descriptions | 2 | 0 | 2 | 0 |
| 4 — Request config / architecture | 5 | 2 | 2 | 1 |
| **Total** | **126** | **40** | **51** | **35** |

Files: ~390 audited, ~245 clean.

---

## Findings — High

| ID | Location | Evidence | Pattern | Why obsolete | Action |
|---|---|---|---|---|---|
| A1 | install-tts-hook.sh:114 | `claude-3-5-haiku-latest` | 4 API fossil | Haiku 3.5 retired 2026-02-19; default summarizer fails silently | rewrite → `claude-haiku-4-5` |
| A-h | hooks/hooks.json:10 | `"timeout": 10000` | 2-volatile | Hook timeout is seconds (~2.8 h) | rewrite → `10` |
| A2 | CLAUDE.md:852-855 | "capabilities that also ship as a skill have NO command file" | 2-volatile/history | `commands/highlight-reel.md`, `codex-prompt.md` exist | rewrite |
| A3 | CLAUDE.md:748, 798-859 | Plugin Structure tree | 2-volatile | Omits 26 of 74 skills, `commands/hook/`, `submodule/`, 7 of 10 agents | rewrite |
| A4 | README.md:19 | "invoked directly by the Skill tool (or by Claude when it recognizes the trigger)" | 2-conflict | Contradicts manual-only policy (newer, enforced by `check-invocation-policy.py`) | rewrite |
| A5 | README.md:44 | "lives in apps/spec-interviewer/" | 2-volatile | No `apps/` dir | remove |
| B1 | commands/knowledge/promote.md:37 | `wiki/verndale/playbooks/` | 2-volatile | Client-specific; vault org folder is chosen at `/wiki:init` | rewrite |
| B2 | commands/wiki-new-client.md:19 | "runs an intake interview" | 2-volatile | Skill has no interview | rewrite |
| B3 | commands/wiki-lint.md:17 | "parses `[--scope …] [--fix]`" | 2-conflict | Skill `report-only` defaults true → `--fix` never fixes | rewrite |
| B4 | commands/db/publish.md:4 | `[--no-deploy]` | 2-volatile | Flag defined nowhere | remove |
| B5 | commands/db/publish.md:22-25 | hand-edit `config.json` + log | 2-conflict | Skill uses `db.py publish-record` (stamps `last_publish`) | rewrite |
| B6 | commands/hook/add-stop.md:32 | "settings scope and idempotency strategy" | 2-conflict | Skill asks scope/language/failure mode | rewrite |
| C1 | skills/agent-loop-audit/SKILL.md:10,55; references/rules.md:178,180; patterns.md:28,117,182 | `session.status.idle` | 2-volatile | Event is `session.status_idle` | rewrite |
| C2 | agent-loop-audit/SKILL.md:55-57; patterns.md:30-36,119-122 | `stop_reason?.kind`, `"completed"`, `pending_tool_call_ids` | 2-volatile | `stop_reason.type` (3 values) + `event_ids` | rewrite |
| C3 | agent-loop-audit/SKILL.md:11,54; rules.md:179; patterns.md:46,126 | "fan events" | 2-volatile | Timing/tokens come from `span.*` events | rewrite |
| C4 | agent-loop-audit/SKILL.md:52; rules.md:176 | "five fixed input event types" | 2-volatile | Six; omits `user.tool_confirmation`, `user.custom_tool_result` | rewrite |
| C5 | skills/architect-agents/references/model-allocation.md:49 | "Opus costs ~5x more than Sonnet" | 2-volatile | Opus 5.5 $4/$20 vs Sonnet 5 $2/$10 = 2x | rewrite |
| C6 | architect-agents/templates/orchestrator-agent.md:11 vs :47-59 | `tools: Read, Bash, Grep, Glob` + "Dispatch agents using the Agent tool" | 2-conflict | Generated orchestrator has no Agent tool | rewrite |
| C7 | skills/biome-guardrails/SKILL.md:279 | "replace the hardcoded `npx` on lines 12 and 21" | 2-volatile | Template now uses `__PMX__` on line 13 | rewrite |
| C8 | biome-guardrails/SKILL.md:295,307 | `"timeout": 5000` / `15000` | 2-volatile | Seconds (~83 min / ~4 h) | rewrite → 5 / 15 |
| C9 | skills/ai-waiting-ux/references/event-mapping.md:18 | "If `stop_reason === 'end_turn'`, the agent loop may continue" | 2-volatile | Inverts `end_turn`/`tool_use`; omits `refusal`/`max_tokens`/`pause_turn` | rewrite |
| C10 | ai-waiting-ux/references/event-mapping.md:41-43; audit-rules.md:19; architecture.md:86 | "When extended thinking is off" | 2-volatile/1d | Thinking on by default; text empty unless `display: "summarized"` | rewrite |
| D1 | skills/glean-agent-toolkit/SKILL.md:201; references/troubleshooting.md:153 | `import openai_agents` | 2-conflict | Own template imports `agents` → doctor false-fails | rewrite |
| D2 | skills/knowledge-loop/SKILL.md:101 | `wiki/verndale/playbooks/` | 2-volatile | Same as B1 | rewrite |
| D3 | knowledge-loop/SKILL.md:35, 75 | "fill its domain→rules map" | 2-volatile | Hook template has no map; lists all domains | rewrite |
| D4 | skills/mcp-server-scaffold/SKILL.md:127 | `templates/<lang>/src/tools/<kind>.*` | 2-volatile | Templates named by example tool, not kind | rewrite |
| D5 | mcp-server-scaffold/SKILL.md:96 | "One example test per tool exists" | 2-conflict | Templates ship 3 (Bun) / 2 (Go) tests | rewrite |
| E1 | skills/microdots-port-feature/SKILL.md:62, 230-233, 241, 246, 268 | "invoke the `new-micro` skill" | 2-volatile | Renamed `microdots-*`; manual-only → load by path | rewrite |
| E2 | microdots-port-feature/references/spec-and-execution.md:72-80,114-116,135 | same | 2-volatile | Same | rewrite |
| E3 | microdots-port-prototype/SKILL.md:143-149 vs microdots-port-app | "`dossier-manifest.json` … names port-app already reads" | 2-conflict | port-app never reads it | add (in port-app) |
| E4 | skills/orchestrate/SKILL.md:141,183; references/subagent-prompts.md:48 | `run_in_background: false` | 2-volatile (tool contract) | Agent tool has no such field | rewrite |
| F1 | skills/setup-plugin/SKILL.md:115,131,255 | "Must be `<namespace>:<command-name>`… Always ask for the namespace prefix" | 2-conflict | Newer :80-82 says never ask; group dir is the namespace | rewrite |
| F2 | setup-plugin/references/plugin-structure.md:102,111,147 | same | 2-conflict | Newer :271-287 | rewrite |
| F3 | setup-plugin/SKILL.md:162; plugin-structure.md:238,252 | "`timeout` (default 10000ms)" | 2-volatile | Seconds; repo's own session-hooks uses seconds | rewrite |
| F4 | skills/session-hooks/templates/start-ai-consultation.py:12,17,102 | `data["content"][0]["text"]`; 400 max_tokens; `claude-opus-4-6` | 4 thinking/max_tokens | Thinking is on by default for current Opus → `content[0]` is a thinking block → KeyError → silent empty; 400 truncates; no refusal check | rewrite |
| G1 | skills/wiki-status/SKILL.md:16 | `WIKI_DIR = ./.claude/wiki` | 2-conflict | Every sibling uses `./wiki` | rewrite |
| G2 | wiki-status/SKILL.md:52 | "## Health Score Summary" | 2-volatile | Lint report has `## Executive Summary` / `**Health Score**` | rewrite |
| G3 | wiki-query/SKILL.md:145; wiki-scaffold-client/SKILL.md:78; references/entity-templates.md | `_schema/TEMPLATES.md` | 2-volatile | wiki-init creates `_schema/templates/<type>.md` | rewrite |
| G4 | skills/ui-issue-to-plan/references/plan-synthesis.md:53 | `/wiki:ingest-document '<plan-path>' spec` | 2-volatile | Missing company arg | rewrite |
| G5 | skills/wiki-to-mcp/SKILL.md:160,201 | `/wiki-mcp:add-tool`, `/wiki-mcp:smoke-test` | 2-volatile | Commands don't exist | rewrite |
| G6 | video-to-deliverables/references/skill-factory-profile.md:342 (+5 sites) | `{PLUGIN_DIR}/plugin.json` | 2-volatile | Manifest lives in `.claude-plugin/` | rewrite |

## Findings — Medium

| ID | Location | Evidence | Pattern | Why | Action |
|---|---|---|---|---|---|
| A6 | CLAUDE.md:40, 694 | "Use the wiki-confluence-reconcile skill" | 2-conflict | Same file :731 forbids Skill-tool dispatch | rewrite |
| A7 | CLAUDE.md:172, 778 | "the session's most capable model (Fable)" | 2-history (pinned model) | Session model is Opus 5.5; stales each release | rewrite |
| A8 | CLAUDE.md:118-680 & 864-911 | Delivery-Recap :507-543 restated at :907 (#37) | 2-duplication + 1c padding | ~34K tokens/session; copies already drift (A2,A3,A7) | remove dup Getting Started items (separate patch); prose relocation = decision |
| A9 | CLAUDE.md:5 | "Do not provide too much explanation." | 1a "don't be too X" | Read literally → under-explains | rewrite |
| A11 | agents/workflow-analyzer.md vs agents/video-to-deliverables.md | near-duplicate role/tools/model | 4 redundant sub-agents | Default profile of video-to-deliverables is `workflow` | remove + fold (see patch notes) |
| A12 | channels/wireframe-feedback/server.ts:122-125 | 2-sentence `reply` description | 3 under-described | Omits unknown-slug failure, 4000-char truncation, append-only | add |
| B7 | commands/ux-audit-{a11y,code,quick,visual}.md:11; codex-prompt.md:11 | "Invoke the ux-audit skill" | 2-conflict | Line 9 forbids Skill tool | rewrite |
| B8 | commands/db/publish.md:19 | `skills/project-db/references/d1-publish.md` | 2-volatile | Doesn't resolve in user project | rewrite `${CLAUDE_PLUGIN_ROOT}/…` |
| B9 | commands/repo-audit.md:108 | "Executive Summary — ≤10 sentences" | 1f numeric ceiling | Caps starve reasoning | rewrite |
| C11 | ai-waiting-ux/references/event-mapping.md:3 | "event names follow the Messages streaming protocol" | 2-volatile | Agent SDK yields SDKMessages; stream events only via `includePartialMessages` | rewrite |
| C12 | agent-loop-audit/references/patterns.md:19-21,108-110 | `client.sessions.connect()`, `stream.send()` | 2-volatile | Real: `client.beta.sessions.events.stream()` then `.send()` | rewrite |
| C13 | architect-agents/references/agent-file-format.md:54-60; SKILL.md:197; templates/implementation-agent.md | "Use **NEVER** and **ALWAYS** bold formatting… Minimum 5" | 1a | Injects pressure language + quota into every generated agent | rewrite |
| C14 | data-ui-craft/SKILL.md:139,150 | "Per the user's earlier choice" | 2-history | Reads as consent from current user | rewrite |
| C15 | ai-waiting-ux/SKILL.md:293; data-ui-craft/SKILL.md:230 | `npx next lint` | 2-volatile | Removed in Next.js 16 (external) | rewrite |
| C16 | codex-prompt-builder/SKILL.md:48 | "AskQuestion/request_user_input" | 2-volatile | Claude Code tool is AskUserQuestion | rewrite |
| C17 | biome-guardrails/SKILL.md:146,184 | unpinned `@biomejs/biome` + 1.9 config | 2-volatile | Biome 2.x config breaks | add migrate step |
| D6 | interactive-wireframe/SKILL.md:122,150 | `$SKILL_DIR` | 2-volatile | Undefined when loaded by path | add definition |
| D7 | mcp-server-scaffold/templates/bun/src/tools/ai-search-companies.ts.tmpl:10,27-29 | `q: z.string()…` no describe | 3 under-described | Exemplar copied into user servers | add |
| D8 | delivery-recap/SKILL.md:216 | "stable favicon" | 2-volatile | Artifact `favicon` deprecated → `icon`; cross-session update needs `url` | rewrite |
| E5 | microdots-port-app/SKILL.md:190-194; spec-and-execution.md:72-77 | `bun run new:microdot <name>` | 2-conflict | Newer microdots-new-micro always names mode + deploy-discovery | rewrite |
| E6 | microdots-port-app/SKILL.md:206-207; spec-and-execution.md:116; standalone-scaffold.md:162 | "The monorepo's verify skill is unavailable here" | 2-conflict | Plugin ships `microdots-verify` for any workspace | rewrite |
| E7 | misunderstanding/SKILL.md:187-188 | `skills/defect-intake/…` | 2-volatile | Repo-root-relative | rewrite |
| E8 | pi-assistant/SKILL.md:19,70,103 | `python3 skills/pi-assistant/scripts/…` | 2-volatile | Same | rewrite |
| E9 | microdots-debug-blank/SKILL.md:161; microdots-design/SKILL.md:65 | "Finish with `microdots-verify`" | 2-conflict | Handoff to manual-only skill with no load path | rewrite |
| F5 | setup-plugin/references/plugin-structure.md:217 | "Minimum 5 constraints, ALWAYS/NEVER formatting" | 1a | Pressure quota in generated agents | rewrite |
| F6 | spec-elicitation/SKILL.md:7,43,69-73 | "**Do not stop early.**" "**ALWAYS** probe" "**NEVER** stop" | 1a booster cluster | Over-interviews on literal model | rewrite |
| F7 | project-db/templates/claude-md-block.standalone.md:3,7 | "MUST use it… before answering **any** project question" | 1a | Installed in always-loaded CLAUDE.md → SQL for trivial questions | rewrite |
| F8 | project-ontology/templates/claude-md-block.{wiki,standalone}.md:11,23-24 | "`/ontology:apply`", "`/ontology:status`" | 2-conflict | Not in invocation allowlist → refused | rewrite to engine CLI |
| F9 | skill-reverse-engineer/SKILL.md:232,318 | "No file is created… before this gate" | 2-conflict | Same file writes report + sidecar earlier | rewrite |
| F10 | proof-of-work/SKILL.md:35-36; sim-data/SKILL.md:38-39; skill-reverse-engineer/SKILL.md:65 | "or implicitly when asking…" | 2-conflict | Manual-only | rewrite |
| F11 | session-hooks/SKILL.md:285; screencast-capture/SKILL.md:171 + convert-and-handoff.md:48; screencast-highlight-reel/SKILL.md:121 | `computer://` links, `present_files` | 2-volatile | Cowork-only mechanisms | rewrite |
| F12 | screencast-capture/references/screen-record-protocol.md:83; SKILL.md:123 | "don't narrate to yourself between calls" | 1d update-suppressor | Batching (`browser_batch`) is the real fix; not loaded | rewrite + add |
| G7 | skill-factory-profile.md:417 vs :525 | emit `${CLAUDE_PLUGIN_ROOT}` vs flag it | 2-conflict (same file) | Validator rejects writer's output | rewrite :525 |
| G8 | wiki-init/SKILL.md:11,21-29,47-50 | "you MUST understand…", "ALWAYS scan", "NEVER hardcode" | 1a/1c | Six emphatic lines restate one rule | rewrite |
| G9 | wiki-lint/references/checks.md:122-123,130-132 | "(An earlier hard-coded list required…)" | 1d migration-relative | Diff against text the model never saw | rewrite |
| G10 | wiki-to-mcp/SKILL.md:52,150-153 | `{SKILL_DIR}` | 2-volatile | Undefined | rewrite |
| G11 | wireframe-parity/references/measurement.md:9 | `$WIREFRAME_SKILL_DIR` | 2-volatile | Undefined | rewrite |
| G12 | workstream-orchestrate/SKILL.md:196 | `args = {…}` without `models` | 2-volatile | `workstream-loop.mjs:18` accepts `models`; roster choice lost | rewrite |
| G13 | wiki-to-mcp/SKILL.md:125,214-222,273,281 | "if running inside Verndale-Agentics" | 2-volatile/history | Origin-repo facts | rewrite |
| G14 | ux-audit/SKILL.md:38,80-86,141; references/report-format.md:4 | `/mnt/user-data/uploads/`, `apt-get install ffmpeg` | 2-volatile | claude.ai sandbox paths; fail on macOS Claude Code | rewrite |
| G15 | video-to-deliverables/SKILL.md:32 | "Full example invocations live in this file's git history" | 2-history | Archaeology | remove |
| G16 | skill-factory-profile.md:599 vs :387/:521 | `namespace:slug` | 2-conflict (same file) | File also says name-sans-namespace | rewrite |
| G17 | worktree-ops/SKILL.md:93 | "the repo already has a merge-worktree skill" | 2-volatile | Host-repo fact in portable skill | rewrite |
| G18 | wiki-query/SKILL.md:17,142 | "search the Verndale wiki" | 2-conflict | wiki-init's newer "never hardcode org" rule | rewrite |
| G19 | wiki-lint/references/discovery.md:19; checks.md:76 | `wiki/clients/{slug}/**` | 2-conflict | Top-level may be projects/teams/domains | rewrite |
| G20 | wireframe-parity/references/resolve-and-parse.md:15 | `references/spec-template.md` | 2-volatile | Lives in interactive-wireframe | rewrite |
| A-dup | (merged) A10 = F4 | | | | |

## Findings — Low / flag (report only, no diff)

| ID | Location | Note |
|---|---|---|
| A13 | CLAUDE.md:441 | Benchmark anecdote in behavior text (2-history) |
| A14 | CLAUDE.md:29-40, 866-870 | Unqualified `/wiki:*` names — resolution unverified |
| A15 | CLAUDE.wiki.md | Stale client file ("Verndale Agentics", "7-dimension"); only referenced from `invocation-policy.json` `why` strings |
| B10 | commands/bun/audit.md:24 vs skills/bun-workspace/SKILL.md:180 | `--fix` scope disagrees; same commit — **decision** |
| B11 | 14 commands | "See `skills/…`" pointers unresolvable outside repo; redundant with loader |
| B12 | commands/repo-audit.md:13-14,126 | "in order — do not skip ahead" choreography |
| B13 | commands/ontology/check.md:18-19; status.md:20 | numeric listing caps (tool-output, low harm) |
| B14 | commands/hook/design.md:34 | "Silently scan" (mild suppressor) |
| B15–17 | commands/disclosure/map.md:29; bun/add.md:4; bun/convert.md:45 | flag/argument drift vs skill |
| C18–19 | ai-waiting-ux/SKILL.md:294; data-ui-craft/SKILL.md:208 | leftover no-op / copied notification line |
| C20 | agent-loop-audit rules.md EL3 | missing: break-on-idle then delete/archive race (keep-list 11 add) |
| C21 | ai-waiting-ux/templates/sdk-adapter.ts.tmpl:24 | `defaultModel = 'claude-sonnet-4-6'` (previous gen) |
| C22–23 | ai-waiting-ux eta-derivation.md:56; chore-crons cron-recipes.md:150 | legacy tokenizer pkg; unverifiable beta header |
| C24 | claude-design-to-app-workflow/SKILL.md:2,20; architect-agents/SKILL.md:65 | un-namespaced invocation names |
| D9–10 | glean-agent-toolkit/SKILL.md:72 vs :248; :244 | self-contradiction (same commit) — **decision** |
| D11–12 | knowledge-loop/SKILL.md:17,31; issue-to-agent/SKILL.md:55,171 | history narratives ("Settled with the user", "June-2026 incident") |
| D13 | issue-to-agent/references/workflows.md:16 | `:*` vs ` *` permission syntax (external, unverified) |
| D14–15 | elevenlabs-transcribe, foundry-*, defect-intake; git-submodules, glean, mcp-server-scaffold, delivery-recap | short `/name` forms; "use proactively" trigger lists contradict manual-only |
| D16 | fast-ci/SKILL.md:116; foundry-consolidate:91; foundry-project:124 | commit without gate — **decision** (plugin-wide commit policy) |
| D17–18 | glean templates; mcp-go pin | non-Anthropic identity stub / undated SDK pin |
| E10–13 | microdots-content:103; port-prototype extraction.md:34; progressive-disclosure:90; large-codebases.md | misattributed rules; migration-relative line; strategy coaching; undated external claims |
| F13 | project-ontology mandate :9 vs SKILL.md:133-135, governance.md, ontology.py:1416 | may agent run `approve` after a user yes? — **decision** |
| F14 | session-hooks:85; project-db:92; project-ontology:85 | "Silently scan / Detect, silently" |
| F15–16 | session-hooks hook-spec.md:65,71,79,101; output-protocol.md:80 | undated Claude Code hook facts (default timeout, SessionEnd reasons) — needs check |
| F17 | project-db/scripts/db.py:1328 | banner hardcodes "200-row cap" while config drives it |
| F18–19 | spec-elicitation:45-52; plugin-structure.md:247 | repeated phase text; incomplete hook-event list |
| G21–27 | workflow-analyzer:132 (≥5 quota); wiki-ingest-meeting:33 (one vault's vocab); finalize.md:27 (prepend vs append); skill-factory :19; wiki-to-mcp:127; worktree-ops:103 (`--confirm`); workflow-analyzer vs video-to-deliverables skills (merge = **decision**) |

## Decisions only you can make

1. **Wiki suite: general-purpose or Verndale-specific?** `wiki-init` says never hardcode org/platform; `wiki-status:31,81`, `wiki-scaffold-client:11-12` (default `Salesforce B2B Commerce`), `finalization.md:52` (`/verndale:migration-pipeline`), `wiki-ingest-meeting:50,64,120` hardcode them.
2. **One `_log.md` format.** Six variants: 5-col table (wiki-init, scaffold-client), 7-col table (wiki-query), `##` sections (ingest-meeting, ingest-document, lint, confluence), bullet (wiki-to-mcp); `wiki-status:45` parses a seventh.
3. **One frontmatter schema.** wiki-init defines `status, source, date` / `status-color`; ingest/confluence/lint use `decision`, `created`, `updated`, `sources`, `category`, `effort`. Lint's stale-page check needs `updated`, which wiki-init pages lack.
4. **Ontology approval** (F13): may the agent run `ontology.py approve --by <name>` after an AskUserQuestion yes, or must the human run it?
5. **Commit policy** (D16): fast-ci / foundry-* commit unprompted; most skills never commit.
6. **Root CLAUDE.md size** (A8): move the long "When to Use …" prose paragraphs to README / SKILL.md and keep one table row each? That's ~25K tokens/session on the branch whose goal is context reduction. The patch set only removes the duplicate "Getting Started" items.
7. **Defect ownership** (flag, user-level): `OPERATING-MANUAL.md:148` "implement fixes only in scope; list the rest" vs `~/.claude/CLAUDE.md` "Nothing gets deferred." Which governs this repo?

## Decisions — resolved 2026-09-28 and implemented

| # | Decision | Implemented |
|---|---|---|
| 1 | Wiki suite is **general-purpose** | Across 27 wiki-suite files, org, client and platform names are replaced by a Vault-layout block in `SCHEMA.md` (grouping folder, platforms, default platform, org section). `wiki/clients/` became `wiki/{group}/`, and examples now use `acme`. |
| 2 | Log format: **`## YYYY-MM-DD — <operation> — <summary>` + body**, appended | Every wiki skill writes this format, and `wiki-status` parses it. The MCP `wiki_append_to_log` tool writes it too. Outside the wiki suite: `session-hooks/templates/stop-wiki-log.sh` wrote a table row and now writes a heading (new test `skills/session-hooks/tests/test_stop_wiki_log.py`, which fails on the old hook). The "append a row" wording in plan-review, wireframe-parity, session-hooks docs and `commands/hook/add-stop.md` is aligned. |
| 3 | Frontmatter: **`created`, `updated`, `sources`, `decision`** | wiki-init's templates and schema are migrated. Ingest, confluence and query read and write only these keys. The lint stale check reads `updated`, and lint flags and fixes the legacy `date`/`source`/`status-color` keys. `decision` values are slugs (`ootb|config|custom|gap|tbd|third-party`), rendered as emoji. |
| 4 | Ontology approve/deprecate are **run by a human** | `ontology.py` block message, SKILL.md, governance.md and enforcement.md are aligned. New test `TestHooks.test_gate_message_asks_the_user_to_run_the_command_not_the_agent_to_approve` fails on the old message. The Bash guard is unchanged. |
| 5 | Skills **never commit unprompted** | fast-ci (+ command), foundry-consolidate and foundry-project now tell the user what to commit and offer to do it on a yes. fast-ci keeps the "reformat alone, then add its SHA to `.git-blame-ignore-revs`" reason. |
| 6 | **Move CLAUDE.md prose to README** | CLAUDE.md shrank from 103,842 to 52,155 bytes. All 131 table rows are byte-identical, 23 sections keep a one-line differentiator, and the prose moved verbatim to README § Skill reference. No `/command` token was lost. |
| 7 | **Global defect rule governs** | `OPERATING-MANUAL.md:148` rewritten: fix defects (with a test) before new work, and stop only when the fix is unsafe or needs the user's decision. Feature-scope creep still needs asking. |
| 8 | Codex hook timeout: **verify units first** | The [Codex hooks docs](https://learn.chatgpt.com/docs/hooks) say "timeout is in seconds", so root `hooks.json` went from `10000` to `10`, and `check-hook-timeouts.py` now scans it (6/6 self-test). `.claude/hooks.json` (`10000`) is left for you, as chosen. |

**Left as is on purpose:** `skills/microdots-new-micro/SKILL.md:339-342` (`status-color`, "a row in `wiki/_log.md`") describes a MicroDots workspace's own wiki, which has its own schema. That is a different vault from the wiki suite.

## Proposed diff

One patch per batch in `reviews/prompt-audit-2026-09-28-patches/`, one finding per logical hunk. All High/Medium findings with a remove/rewrite/move/add action are included; `flag`, Low, and the **Decisions** above are not. Every patch passes `git apply --check -p1` against the working tree, individually and as one combined set (89 files, 171 hunks). Applied 2026-09-28; to revert, run `git apply -R reviews/prompt-audit-2026-09-28-patches/*.patch`.

| Patch | Findings | Files | Hunks | Notes |
|---|---|---|---|---|
| `A.patch` | A1–A7, A9, A11, A12, hooks.json timeout | 7 | 16 | A11 deletes `agents/workflow-analyzer.md` (grep: nothing dispatches it) and folds its one extra constraint into `video-to-deliverables.md` |
| `A-claude-md-dedupe.patch` | A8 (partial) | 1 | 1 | Removes Getting Started items 11–39, which restate the "When to Use" sections. Prose relocation is Decision 6 |
| `B.patch` | B1–B9 | 11 | 12 | B3 is the command-side fix (`--fix` ⇒ `report-only=false`) |
| `C.patch` | C1–C17 | 17 | 35 | Managed Agents facts verified against bundled API docs. Teardown example closes by leaving the `for await` loop, not an unverified `abort()` call |
| `D.patch` | D1–D8 | 7 | 10 | D7 puts the parameter contract in the description, because the template sends clients only `{type:"object"}` |
| `E.patch` | E1–E9 | 11 | 24 | |
| `F.patch` | F1–F12 | 16 | 33 | F4 only changes the Anthropic branch (`max(max_tokens, 4000)`, text-block extraction, refusal → None). `py_compile` passes |
| `G.patch` | G1–G20 | 19 | 40 | |

Apply everything: `git apply reviews/prompt-audit-2026-09-28-patches/*.patch`. Or pick individual files or hunks (`git apply --include=<path>`).

## Applied and verified (Step 7)

**Follow-up fix found while writing the guard:** both installed ontology mandate blocks and the generated `ONTOLOGY.md` still offered `/ontology:deprecate` to the agent with no human label. This is the same defect as F8. The rows are now labelled `(the user decides)` / `(human)` in `claude-md-block.{wiki,standalone}.md:22` and `ontology.py:2126`.

**Regression guards added.** Each one fails on the pre-audit tree:

| Guard | Catches | Proof |
|---|---|---|
| `scripts/check-hook-timeouts.py` (+ `--self-test`, wired into `.github/workflows/invocation-policy.yml`) | a Claude Code hook `timeout` > 600 in `hooks/hooks.json` or any skill file (ms instead of s) | 5/5 self-test cases; the pre-audit `10000` fails it |
| `test_ontology.py::TestInitInstall::test_installed_text_offers_agents_only_invocable_commands` | installed mandate / `ONTOLOGY.md` pointing the agent at a manual-only `/ontology:` command without handing it to a person | tamper: re-adding a `/ontology:apply` row fails it |
| `skills/session-hooks/tests/test_start_ai_consultation.py` | the consultation hook reading a thinking block as the answer, or sizing `max_tokens` without room for thinking | 5 tests pass; 2 fail on the pre-audit template |

**Gates after applying (all exit 0):**
- `check-invocation-policy.py`, plus its 8/8 tamper cases
- `check-hook-timeouts.py`, plus its 5/5 self-test cases
- `validate-marketplace.py`, plus its 11/11 tamper cases
- `test_ontology.py` 60/60
- `test_db.py` 23/23
- `test_start_ai_consultation.py` 5/5
- `bash -n install-tts-hook.sh`, `py_compile`, and `hooks/hooks.json` parses

**Not verified:**
- **Behaviour.** No skill was run end to end after the edits, so every prompt-text change is an untested hypothesis until it runs (Step 7).
- **`/wiki:lint --fix`.** It was not exercised on a scratch vault.

**Flagged, not edited:**
- Root `hooks.json:10` (`"timeout": 10000`) is the **Codex** manifest's hook file (`.codex-plugin/plugin.json:31`). I have not verified what timeout unit Codex expects.
- `.claude/hooks.json:10` (`10000`) is local agent configuration, which the audit does not edit.

