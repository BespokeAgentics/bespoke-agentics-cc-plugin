<!--
Template: per-subsystem CLAUDE.md (one per inventoried package/service/subsystem).
Fill {{PLACEHOLDERS}} from that subsystem's Directory Profile. Only the managed block
is regenerated on refresh; preserve anything outside it. Keep it tight — this loads
on demand when Claude works here, on top of the root file, so don't repeat repo-wide
rules. Capture what a newcomer to THIS area would get wrong.
-->

<!-- progressive-disclosure:managed -->
# {{SUBSYSTEM_NAME}}

{{ONE_LINE_PURPOSE}}

**Stack:** {{STACK}}  <!-- languages, frameworks, runtimes, notable libs -->

## Commands

- Build: `{{BUILD_CMD}}`
- Test: `{{TEST_CMD}}`  (single file: `{{TEST_ONE_FILE_CMD}}`)
- Lint: `{{LINT_CMD}}`
- Typecheck: `{{TYPECHECK_CMD}}`
- Dev/run: `{{DEV_CMD}}`
{{#if HAS_MIGRATIONS}}- Migrations: `{{MIGRATE_CMD}}`{{/if}}
{{#if HAS_ENV}}- Env: {{ENV_SETUP}}{{/if}}

## Layout & conventions

{{LAYOUT_NOTES}}  <!-- where routes/components/models/tests live; entry points; naming patterns -->

{{#each CONVENTIONS}}
- {{this}}
{{/each}}

## Testing

{{TESTING_NOTES}}  <!-- framework, where tests live, how to run one -->

{{#if GOTCHAS}}
## Gotchas

{{#each GOTCHAS}}
- {{this}}
{{/each}}
{{/if}}

{{#if DEPENDS_ON}}
## Depends on

This subsystem imports: {{DEPENDS_ON_LIST}}. Those packages are granted via
`additionalDirectories` in this directory's `.claude/settings.json` for cross-package edits.
{{/if}}

{{#if WIKI_LINKS}}
## See also

{{#each WIKI_LINKS}}
- {{link}} — {{why}}
{{/each}}
{{/if}}
<!-- /progressive-disclosure:managed -->
