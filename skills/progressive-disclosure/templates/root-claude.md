<!--
Template: root CLAUDE.md
Fill the {{PLACEHOLDERS}}. Everything between the managed sentinels is owned by
progressive-disclosure and is safe to regenerate on refresh; anything OUTSIDE the
sentinels is hand-written and must be preserved on merge. If a CLAUDE.md already
exists, replace only the managed block and leave the rest untouched.
-->

<!-- progressive-disclosure:managed -->
# {{PROJECT_NAME}}

{{ONE_PARAGRAPH_OVERVIEW}}

## Repository layout

{{REPO_TYPE_SENTENCE}}  <!-- e.g. "This is a pnpm monorepo with N packages under packages/:" or "Single-tree app; major subsystems live under src/:" -->

{{#each SUBSYSTEMS}}
- `{{path}}` — {{purpose}} ({{stack_summary}})
{{/each}}

{{RUN_LOCATION_RULE}}  <!-- e.g. "Run commands from the package directory, not the repo root. Each package has its own manifest and test suite." -->

## Conventions that apply everywhere

- {{COMMIT_PR_CONVENTIONS}}
- {{CODING_STANDARDS}}
- {{ANY_REPO_WIDE_RULES}}

## Context layer

This repo uses layered memory files. Each package/subsystem has its own `CLAUDE.md`
with local stack, commands, and conventions — it loads when you work in that area.
`AGENTS.md` in each directory points to that directory's `CLAUDE.md`.

{{#if HAS_WIKI}}
## Knowledge base (wiki-first)

{{WIKI_MANDATE_LINE}}  <!-- Restate the host's wiki-first rule briefly if one exists. -->
Start at [[_index]] (`wiki/_index.md`). Query the wiki before answering project
questions; update it after content-producing work. Key references:
{{#each WIKI_KEY_LINKS}}
- {{link}} — {{why}}
{{/each}}
{{/if}}

{{#if HAS_ARCHITECT_AGENTS}}
## Agent team

Agent and command definitions for this repo live in `.claude/agents/` and
`.claude/commands/` (see `.claude/_architecture.md`). This file is the *context*
layer; that is the *agent* layer.
{{/if}}
<!-- /progressive-disclosure:managed -->
