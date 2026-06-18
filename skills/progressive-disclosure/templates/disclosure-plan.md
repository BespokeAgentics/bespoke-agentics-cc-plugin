<!--
Template: the dry-run plan written to <root>/.claude/disclosure-plan.md in Phase 3.
This is the contract the user approves before anything is written to the repo proper.
Mirror it in chat. Fill {{PLACEHOLDERS}}; drop sections that don't apply.
-->

# Progressive Disclosure — Plan

- **Root scanned:** `{{ROOT}}`
- **Workspace type:** {{WORKSPACE_TYPE}}
- **Depth:** {{DEPTH}}
- **Mode:** {{MODE}}
- **Generated:** {{DATE}}
- **Working tree:** {{CLEAN_OR_DIRTY}}

Nothing below is written until you approve. Reply "apply all", or tell me what to skip
(e.g. "memory files only", "skip settings", "exclude package X").

## Summary

| Action | Count |
| --- | --- |
| CREATE | {{N_CREATE}} |
| UPDATE | {{N_UPDATE}} |
| SKIP (already correct) | {{N_SKIP}} |

## Memory files — root

| File | Action | Rationale |
| --- | --- | --- |
| `CLAUDE.md` | {{ACTION}} | {{WHY}} |
| `AGENTS.md` | {{ACTION}} | pointer → ./CLAUDE.md |

{{#if UPDATE}}<details><summary>Diff: root CLAUDE.md (managed block)</summary>

```diff
{{ROOT_CLAUDE_DIFF}}
```
</details>{{/if}}

## Memory files — per subsystem

{{#each SUBSYSTEMS}}
### `{{path}}`
| File | Action | Rationale |
| --- | --- | --- |
| `{{path}}/CLAUDE.md` | {{action}} | {{why}} |
| `{{path}}/AGENTS.md` | {{action}} | pointer → ./CLAUDE.md |

{{#if diff}}<details><summary>Diff</summary>

```diff
{{diff}}
```
</details>{{/if}}
{{/each}}

## Settings changes

Shown as the **merged result** (existing keys preserved). Per-subsystem settings files
are listed where people launch from those directories.

<details><summary>`{{SETTINGS_PATH}}` (merged)</summary>

```json
{{MERGED_SETTINGS_JSON}}
```
</details>

- **Read deny rules:** {{DENY_SUMMARY}}
- **additionalDirectories:** {{ADDL_DIRS_SUMMARY}}
- **claudeMdExcludes (suggested — confirm):** {{EXCLUDES_SUMMARY}}

## SessionStart hook

- Script: `.claude/hooks/disclosure-context.sh` — {{ACTION}}
- Registered in: `{{SETTINGS_PATH}}` → `hooks.SessionStart`
- Surfaces per-launch-dir context for: {{HOOK_MAPPED_DIRS}}

## Code-intelligence recommendations

These are suggestions you install (not auto-applied):
{{#each LSP_RECS}}
- {{language}}: `{{install_cmd}}`
{{/each}}

## Wiki updates

{{#if HAS_WIKI}}
- `wiki/_log.md` — append operation entry
- {{WIKI_PAGE_NOTE}}
{{else}}
No wiki detected — skipped.
{{/if}}

## Notes & risks

{{NOTES}}
