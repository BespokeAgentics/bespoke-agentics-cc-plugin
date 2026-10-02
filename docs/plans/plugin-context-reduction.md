# plugin-context-reduction — trim the standing listing cost, then split the plugin into family plugins

**Status:** Phase A **done 2026-09-21, released 2026-10-02 as v2.9.0** (committed on
`feat/plugin-context-reduction`; not yet pushed or merged), in a stronger form than planned — the plugin
is now **manual-only** (model-visible listing 70,711 → 1,901 chars; measured +10,259 → +2,131 tokens per
session). Phase B (family plugins) is **not started and no longer justified by context cost** — see
"Phase B — reassessed".
**Requested:** 2026-09-21.

## The ask

Too much context is loaded per turn when the plugin is enabled. Explore ways to split the skills up.
Five options were weighed (family plugins, trim in place, `paths:` gating, router skills, user-side
`skillOverrides` presets); the chosen sequence is **Phase A — trim in place**, then **Phase B — split
into family plugins**. The other three are recorded under "Not chosen".

## Evidence (measured 2026-09-21, v2.8.0 @ `7803e32`)

Only the **listing tier** is a standing cost. Skill bodies (856k chars) load on invocation and are not
the problem; nothing in this plan touches them.

| Source | Count | Description chars | ~Tokens |
|---|---|---|---|
| Skills (`skills/*/SKILL.md`) | 73 | 53,769 (52,889 after the 1,536-char listing cap) | ~13.4k |
| Commands (`commands/**/*.md`) | 60 | 16,942 | ~4.2k |
| Agents (`agents/*.md`) | 10 | 3,335 | ~0.8k |

Skill description length distribution:

| Length | Skills | Chars | Share |
|---|---|---|---|
| > 1,536 (tail never reaches the model) | 6 | 10,096 | 19% |
| 1,001 – 1,536 | 17 | 21,762 | 40% |
| 401 – 1,000 | 18 | 15,146 | 28% |
| ≤ 400 | 32 | 6,765 | 13% |

- The 23 skills over 1,000 chars hold 59% of the cost. Capping every description at 400 chars gives at
  most 23,165 chars (−57%); at 300, 18,877 (−65%).
- Over the cap today: `skill-reverse-engineer` 2,184 · `microdots-port-feature` 1,692 ·
  `microdots-port-app` 1,623 · `interactive-wireframe` 1,615 · `data-ui-craft` 1,598 ·
  `delivery-recap` 1,580.
- Commands: none sets `disable-model-invocation`; 49 of 60 are thin (< 2.5k body) and 51 reference the
  skill they wrap, so one capability lists twice (`agentnative:fast-ci` and `fast-ci`). Nine stand alone:
  `agentnative/suite`, `codex-prompt`, `funcspec-status`, `prune-node-modules`, `repo-audit`,
  `ux-audit-{a11y,code,quick,visual}`.
- Frontmatter keys in use across all skills: `name`, `description`, `args`, `argument-hint`,
  `disable-model-invocation` (2 skills: `microdots-new-micro`, `microdots-deploy`). No `paths:`, no
  `when_to_use`.
- **Observed, cause unconfirmed:** in a session with this plugin enabled alongside many others, most
  `bespoke-agentics:*` listing entries rendered name-only. The practical harm today is likely degraded
  auto-triggering as much as tokens.

Split feasibility:

| Family | Skills | Description chars |
|---|---|---|
| build / orchestration | 12 | 15,822 |
| ui-design | 11 | 10,805 |
| microdots | 10 | 7,653 |
| repo-tooling / other | 14 | 6,220 |
| agentnative | 6 | 5,533 |
| wiki + knowledge + db + ontology | 12 | 4,552 |
| video / screencast | 8 | 3,877 |

- File-path references between skills stay inside families (video → `extract-video-frames` /
  `dedupe-frames` / `elevenlabs-transcribe`; `reimagine` → `wireframe-parity`; `misunderstanding` →
  `defect-intake`; `microdots-content` → `microdots-brand-recap`; `screencast-capture` →
  `screencast-highlight-reel`). **One crosses:** `video-to-deliverables` → `architect-agents`
  (`skills/video-to-deliverables/references/skill-factory-profile.md:485`). The
  `skill-reverse-engineer` and `setup-plugin` hits are eval fixtures and a naming example, not runtime
  dependencies.
- 113 name-only mentions across 48 skills ("pair with `plan-review`") — prose, not paths.
- The plugin name is the invocation namespace. `bespoke-agentics:` occurs 155 times in 33 files
  (skills 71, CLAUDE.md 64, docs 13, README 5, commands 2); two are `subagent_type` strings
  (`bespoke-agentics:video-to-deliverables`, `bespoke-agentics:ai-transparency`).
- `hooks.json` runs `scripts/ai-transparency-check.sh` on every `Write|Edit|MultiEdit` for every user
  of the plugin; it belongs to one family (ui-design).

## What the docs confirm (checked 2026-09-21, code.claude.com/docs)

| Claim | Status |
|---|---|
| Listing holds name + description; `description` + `when_to_use` truncated at 1,536 chars | confirmed (skills) |
| `disable-model-invocation: true` takes the description out of context; `/name` still works | confirmed (skills) |
| Marketplace entry may carry `skills` / `commands` / `agents` arrays; `strict: false` makes the entry the whole definition and "conflicts with `plugin.json` fail" | confirmed (plugin-marketplaces) |
| In `plugin.json`, `skills` supplements the default directory; `commands`, `agents`, `hooks` replace theirs | confirmed (plugins-reference) |
| `dependencies: { "name@marketplace": "^1.0.0" }` | confirmed (plugin-marketplaces) |
| `skillOverrides`: `on` / `name-only` / `user-invocable-only` / `off` | confirmed (skills) |
| Subagent descriptions load every session, 15,000-token combined budget | confirmed (sub-agents) |
| `paths:` frontmatter gates a skill on matching files (v2.1.246+) | confirmed (skills) |
| `disable-model-invocation` works on commands and removes them from the model's listing | not documented — **proven 2026-09-21** (probe T1, e2e E1) |
| A command's `Skill(x)` call on a flagged skill is refused ("cannot be used with Skill tool due to disable-model-invocation") | **proven** (T2, E4) |
| `${CLAUDE_PLUGIN_ROOT}` is substituted in command bodies and in agent bodies; a SKILL.md read by path arrives raw | **proven** (T3b, T9) |
| A flagged skill and an open command may share a name: `/name` and the model's Skill call both reach the command | **proven** (T7, T8) |
| Listing budget size and overflow behavior (name-only rendering) | **not documented** |
| With `source: "./"` the plugin cache holds the whole repo, so `${CLAUDE_PLUGIN_ROOT}/skills/<other-family>/` still resolves | **inferred — prove in the B-0 spike** |

## Settled decisions

| # | Question | Decision |
|---|---|---|
| 1 | Sequence | **A then B.** Trimming changes nothing for users and shrinks every family before it is cut out. |
| 2 | Skill bodies | **Untouched.** They are not a standing cost. |
| 3 | Directory moves in Phase B | **None.** Families are marketplace entries over `source: "./"`, not folders. |
| 4 | Triggers (2026-09-21) | **"We should not have any triggers besides manual invocation."** Every skill and command carries `disable-model-invocation: true`, except commands that text the plugin installs into a user's project tells an agent to run unprompted. |
| 5 | The exception list | Eight **commands**, not skills — the names the mandates actually use: `wiki:query`, `wiki:ingest-meeting`, `wiki:ingest-document`, `knowledge:review`, `knowledge:extract`, `db:sync`, `ontology:check`, `ontology:propose`. Each with its reason in `scripts/invocation-policy.json`. `ontology:approve` / `deprecate` stay manual: approval is a human gate by design. |
| 6 | Internal composition | **Load by path, behavior-preserving.** A wrapper command, a conductor, an agent, or a handoff the user accepted reads `${CLAUDE_PLUGIN_ROOT}/skills/<x>/SKILL.md` instead of calling the Skill tool. The policy is about what *triggers*, not about what a user-started workflow may compose. |

## Open decisions

| # | Blocks | Question | Recommendation |
|---|---|---|---|
| B1 | B | What existing `bespoke-agentics` installs become | **Additive for one release:** keep `bespoke-agentics` as the full bundle, add family entries beside it, document "install the bundle *or* families, not both". Slim the bundle at 3.0.0. A meta-plugin that depends on every family saves nothing. |
| B2 | B | Family plugin names = new namespaces (`/bespoke-agentics:plan-review` → `/<family>:plan-review`) | Short `ba-*` names (`ba-wiki`, `ba-build`, `ba-ui`, `ba-video`, `ba-microdots`, `ba-agentnative`, `ba-repo`). Under B1-additive the bundle keeps the old namespace, so nothing breaks until 3.0.0. |
| B3 | B | Versioning | **One version for every local entry**, bumped together. Per-family versions buy nothing while they ship from one commit. |
| B4 | B | Family boundaries | The seven above. `spec-elicitation`, `plan-review`, `orchestrate` stay together in `ba-build`; shared video preprocessing stays in `ba-video`. |

## Phase A — manual-only (done 2026-09-21)

The planned description trim became moot the moment the policy was set: a flagged skill's description
is not in context at all, so its length costs nothing. What was built instead:

| Change | Count |
|---|---|
| Skills flagged `disable-model-invocation: true` | 73 of 73 (2 already were) |
| Commands flagged | 52 of 60; 8 stay model-invocable by policy |
| Commands switched from `Skill(x)` dispatch to loading `SKILL.md` by path | 57 (`agentnative:suite` loads each dimension at its turn; `bun:convert` sends submodule children to `/submodule:convert`) |
| Skill-to-skill handoffs switched to load-by-path | `microdots-port-app` / `-port-feature` → `spec-elicitation`; `microdots-port-prototype` → `microdots-port-app`; `screencast-capture` → `screencast-highlight-reel`; `microdots-new-micro` → `microdots-verify` |
| Offered handoffs told how to load on a yes | `reimagine`, `microdots-port-app`, `microdots-port-feature`, `ai-native-sdlc` |
| `agents/wiki-pipeline.md` | "How to run a step" table mapping each `Command:` / `Skill:` block to a SKILL.md path |
| `defect-intake`, `misunderstanding` descriptions | rewritten (~330 chars): they promised phrase-triggering ("you misunderstood") that the flag ends |

**Defect found and fixed on the way:** `agents/wiki-pipeline.md` dispatched `Skill: wiki-generate-index`
in two workflows; no such skill has ever existed in this repo. Both steps now tell the agent to write
the index itself, following `skills/wiki-init/references/schema-and-templates.md` (Step 6a) and
`skills/wiki-scaffold-client/references/finalization.md` (Step 6). P4 of the new guard fails on any
loader path that names a missing skill.

**Guard.** `scripts/check-invocation-policy.py` (stdlib; P1 flag coverage, P2 command coverage +
allowlist integrity, P3 dead dispatch, P4 loader targets, P5 listing budget of 3,000 chars) with
`scripts/test-check-invocation-policy.py` (baseline + 8 tamper cases) and
`.github/workflows/invocation-policy.yml`, triggered by `skills/**`, `commands/**`, `agents/**`. A new
skill or command now fails CI until it is flagged or deliberately allowlisted with a reason.

### Verification (2026-09-21, Claude Code 2.1.278, headless, `--plugin-dir`, user settings off)

| Check | Result |
|---|---|
| Probe T1: flagged skill and flagged command absent from the model's listing | pass |
| Probe T2: command → `Skill(flagged)` | refused, as predicted — the rewrite was necessary |
| Probe T3b / T9: `${CLAUDE_PLUGIN_ROOT}` substituted in command and agent bodies; relative `references/` path resolved from a by-path load | pass |
| Probe T7 / T8: same-named flagged skill + open command | `/name` and the model's Skill call both run the command |
| E1: entries from this plugin in the model's listing | **exactly 8**, the allowlist |
| E2: `/bespoke-agentics:wiki-status` (flagged command → flagged skill by path) | read `skills/wiki-status/SKILL.md`, ran, no refusal |
| E3: model calls Skill `bespoke-agentics:wiki-query` (the agent-run path the mandate depends on) | command ran, loaded the skill by path, no refusal |
| E4: model calls Skill `bespoke-agentics:plan-review` | refused — no auto-trigger |
| `check-invocation-policy.py` | holds: 73 skills, 52 + 8 commands, listing 1,901 chars |
| Tamper tests | 8/8 caught (policy), 11/11 caught (marketplace); all 3 marketplace entries install-clean |

**Not verified:** no full interactive run of a long workflow (`orchestrate`, `reimagine`, a video skill)
was driven through a by-path load; E2/E3 exercise the mechanism on short skills. 22 SKILL.md bodies
use `$ARGUMENTS`, which arrives unsubstituted on a by-path load — the loader note tells the model the
arguments are the command's, and T3b shows that is honored, but only on the probe.

**What still costs context:** the 8 allowlisted commands and the 9 agent descriptions. Agents have no
equivalent flag (re-checked 2026-10-02 against the sub-agents docs: no frontmatter key hides a
description) and the skills launch them by `subagent_type`.

### Measured in tokens (2026-10-02, Claude Code 2.1.287, headless, user settings off, empty cwd)

Input tokens of a one-word turn, minus the same turn with no plugin (14,272). Deterministic; ablations
run on a copy of the working tree.

| Arm | Added tokens |
|---|---|
| Installed v2.8.0 (`36d825b`, what a user has today) | **+10,259** |
| Working tree, manual-only | **+2,131** |
| ...of which 9 agents (name, description, tool list) | ~1,370 |
| ...of which 8 allowlisted commands | 758 |
| Working tree, agents removed and all 60 commands flagged | **+0** |

- The 73 flagged skills and 52 flagged commands cost exactly nothing.
- `claude plugin details` projects ~21.7k "always-on" for the working tree and ~22.3k for v2.8.0: it
  sums every description and ignores `disable-model-invocation`. Do not use it to judge this plugin.
- A session that also loads other plugins shares one listing budget, so v2.8.0 shows up as less than
  10k there (about 6k was reported) with descriptions cut to name-only.

**User-visible change:** nothing in the plugin auto-triggers from conversation any more. Every
capability is reached by typing its `/name`. Descriptions still appear in the `/` menu.

## Phase B — reassessed

Phase B was chosen to cut context cost. After Phase A the whole plugin's model-visible listing is 1,901
chars, so a split can no longer save anything meaningful there. What a split would still buy:
the `ai-transparency-check.sh` PostToolUse hook stops running on every Write/Edit for users who never
wanted the ui family (B-5), smaller installs, and clearer namespaces — against the costs already listed
(155 namespace references, validator and version-hook changes, two unproven mechanics). **Recommendation:
do not start Phase B for context reasons; decide it on those merits, or move the hook alone.** The design
below is kept for that decision.

## Phase B — family plugins (design, not started)

**B-0 Spike before anything else** (throwaway branch, one family — `ba-wiki`): prove or refute
(1) a `strict: false` entry over `source: "./"` coexists with the root `plugin.json`, or what must
change when the docs' "conflicts fail" applies; (2) the cache holds the whole repo so cross-family
`${CLAUDE_PLUGIN_ROOT}` paths resolve; (3) hooks can be declared per entry; (4) the entry name is the
invocation namespace; (5) a wiki-only install lists only the wiki family. Results go in this plan. If
(1) or (2) fails, the fallback is real subdirectories (`plugins/<family>/`) with shared scripts
vendored — a larger change that would need its own decision.

**B-1 One source of truth.** `.claude-plugin/families.json` maps every skill, command, agent and hook
to exactly one family (a command goes with the skill it wraps). `scripts/build-marketplace.py`
generates the marketplace entries from it, so the arrays cannot drift by hand.

**B-2 Validator.** `scripts/validate-marketplace.py` `check_manifest` (lines 111–140) requires the
local `plugin.json` name to equal the entry name and treats `skills` as one string path; family
entries fail both. Teach it `strict: false` entries with array paths. New tamper cases: a skill in two
families, a skill in none, an array path that does not exist, a `dependencies` target that is not an
entry, generated entries out of date with `families.json`.

**B-3 Version hook.** `.claude/hooks/bump-version.sh` bumps `.version` and `.plugins[0].version` only;
it must bump every local entry (B3) or parity check C5 fails on the first commit.

**B-4 Cross-family edge.** `video-to-deliverables` → `architect-agents`: declare a `dependencies`
entry from `ba-video` to `ba-repo`, or make the reference conditional on the file existing — whichever
the spike shows is cheaper.

**B-5 Hook placement.** Move the `ai-transparency-check.sh` PostToolUse hook to the `ba-ui` entry so
it stops running for users who never installed that family.

**B-6 Docs.** README install section (bundle *or* families), CLAUDE.md "Plugin Structure", and — at
3.0.0, not before — the 155 `bespoke-agentics:` namespace references.

## Work breakdown

| # | Item | State |
|---|---|---|
| 1 | Mechanics probe (flag on commands, refusal, placeholder substitution, name collision) | done |
| 2 | Flag 73 skills, 52 commands; allowlist 8 with reasons | done |
| 3 | 57 commands, 5 handoffs, 4 offered handoffs, 1 agent → load by path | done |
| 4 | `check-invocation-policy.py` + tamper test + CI workflow | done |
| 5 | End-to-end checks E1–E4 against the real plugin | done |
| 6 | Commit, version bump, release notes that say auto-triggering is gone | done 2026-10-02 — v2.9.0; push, merge and reinstall still open |
| 7 | Phase B: decide on its remaining merits (hook placement, install size, namespaces) | open |
| 8 | Agent frontmatter: `allowed-tools` → `tools` on 6 agents, ghost `workflow-analyzer.md` removed, guard P6 | done 2026-10-02 |

## Acceptance

- **A (met):** model-visible listing ≤ 3,000 chars — measured 1,901, from 70,711; the model's listing
  shows exactly the 8 allowlisted commands; a flagged skill refuses the Skill tool; wrapper commands
  and the agent-run path still reach their skills; the guard runs in CI and its tamper tests prove it
  fails on each regression.
- **B:** spike results recorded here; every skill, command, agent and hook in exactly one family;
  a `ba-wiki`-only install lists wiki-family entries and nothing else; validator and tamper tests green
  in CI; every entry install-clean; the full bundle still installs and behaves as before.

## Agent defects found while measuring (fixed 2026-10-02)

- **Tool limits were never in force.** Seven agents declared `allowed-tools:`, a skill/command key the
  harness does not read on an agent; a listing probe showed each as `(Tools: All tools)`. Six now use
  `tools:`. Three of the declared lists also left out `Write` although the body tells the agent to write
  its result to `output_path` (`page-evaluator`, `prototype-screen-analyst`, `ui-frame-analyst`); `Write`
  is added, since enforcing the list as written would have broken them. `wiki-pipeline` had its inert
  line removed and still inherits every tool: the wiki skills it loads use `AskUserQuestion`, which its
  declared list would have cut. Re-probe: all six show their lists.
- **Ghost agent.** Prompt-audit patch A11 (2026-09-28) meant to delete `agents/workflow-analyzer.md` and
  left it as a 0-byte file, which the harness still registered as `bespoke-agentics:workflow-analyzer`
  with every tool and no description. Removed.
- **Guard.** P6 in `check-invocation-policy.py`: every agent has a name and a description and uses only
  frontmatter keys the harness reads. Two tamper cases (10/10 caught); the check reports 8 failures on
  the pre-fix agents.
- **Not verified:** a full `funcspec`, `ui-issue-to-plan` or design-to-app run with the limits now
  enforced. The lists cover every tool the agent bodies name.

## Not chosen

| Option | Why not now |
|---|---|
| `paths:` gating | Cannot gate `*-init` skills (the files do not exist yet), and "lint the wiki" as a first message touches no file. Revisit per family after B. |
| Router skills (10 `microdots-*` → 1) | Loses per-verb auto-triggering and direct `/name`; costs more on every invocation. |
| `skillOverrides` presets | Helps only users who apply them; the default stays heavy. Could ship later through `setup-plugin`. |

## History

- 2026-09-21 — options explored with measurements and a docs check; "2 then 1" chosen; plan written.
- 2026-09-21 — A2 answered "flag them — no triggers besides manual invocation"; scope confirmed as
  plugin-wide minus agent-run. A probe plugin settled four undocumented mechanics before any command was
  touched; the exception list became eight commands rather than skills because the flag works on
  commands and the mandates name commands. Phase A built, guarded and verified the same day.
- 2026-10-02 — cost measured in tokens instead of chars: v2.8.0 +10,259, working tree +2,131, floor 0.
  Two agent defects found on the way and fixed (inert `allowed-tools`, a 0-byte ghost agent); guard P6.
- 2026-10-02 — released as v2.9.0 in one commit with the 2026-09-28 prompt-audit changes, which touch
  the same files and could not be separated. 2.9.0, not 3.0.0: B1 reserves 3.0.0 for slimming the bundle.
  All 10 gates green before the commit.
