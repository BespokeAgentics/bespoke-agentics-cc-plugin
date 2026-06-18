# Settings recipes

Exact shapes for the `.claude/` artifacts this skill produces. Always **deep-merge** into existing files — preserve keys you didn't add, and only touch what the plan listed. Validate JSON parses after every write.

## Where settings live (important)

Project settings in `.claude/settings.json` load **only from the directory Claude is started in** — they are not inherited from parent directories the way `CLAUDE.md` files are. Consequences:

- The **root** `.claude/settings.json` applies to sessions started at the root.
- A **subsystem** that people launch from directly needs its **own** `.claude/settings.json` carrying the deny rules and `additionalDirectories` it requires.
- Inside a worktree, the working directory is the worktree root, so deny rules needed in worktree sessions must also live in the **root** `.claude/settings.json`.
- Personal-only settings go in `.claude/settings.local.json` (gitignored). Use this for `claudeMdExcludes` you don't want to impose on the team. Arrays merge across scopes.

## Read deny rules

Block reads of *checked-in* generated/vendored code (`.gitignore`d paths are already excluded from search). Glob syntax, relative to the settings file's directory.

```json
{
  "permissions": {
    "deny": [
      "Read(./**/dist/**)",
      "Read(./**/build/**)",
      "Read(./**/*.generated.*)",
      "Read(./**/__generated__/**)",
      "Read(./vendor/**)"
    ]
  }
}
```

Build the list from the union of every subsystem profile's **Do-not-read** entries. Don't add paths already covered by `.gitignore` unless they're checked in anyway.

## claudeMdExcludes

Skip loading `CLAUDE.md`/rules for subtrees the user never works in (legacy, other-team, vendored). Glob matched against absolute paths, so start anywhere-patterns with `**/`. Present these as **suggestions** in the plan — they're a judgment call the user should confirm. Prefer `.claude/settings.local.json` unless the team agrees.

```json
{
  "claudeMdExcludes": [
    "**/packages/legacy-*/**",
    "**/packages/admin-dashboard/**",
    "**/packages/*/CLAUDE.md"
  ]
}
```

`"**/packages/*/CLAUDE.md"` excludes every package's file while keeping the root. Managed-policy CLAUDE.md files cannot be excluded.

## additionalDirectories

Derive from the dependency graph: a session in package A that imports package B benefits from access to B. Relative paths resolve against the start directory, so these belong in **the subsystem's own** `.claude/settings.json`.

```json
{
  "permissions": {
    "additionalDirectories": ["../shared", "../web"]
  }
}
```

Note for the plan: the `additionalDirectories` *setting* grants file access only — it does **not** load B's `CLAUDE.md`, rules, or skills. If the user wants B's context loaded too, that's `--add-dir ../shared` at launch (loads skills; loads CLAUDE.md/rules only with `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`).

## Worktree sparse paths (opt-in)

Offer this when worktrees/subagent isolation are in use. List directories (not files); root-level files are always checked out. Include `.claude` to get root settings/skills inside the worktree.

```json
{
  "worktree": {
    "sparsePaths": [".claude", "packages/api", "packages/shared"],
    "symlinkDirectories": ["node_modules"]
  }
}
```

## Code-intelligence recommendation

Not a settings write — a recommendation surfaced in the report. Map detected languages to official plugins:

| Language | Install command |
| --- | --- |
| TypeScript / JavaScript | `/plugin install typescript-lsp@claude-plugins-official` |
| Python | `/plugin install python-lsp@claude-plugins-official` |
| Go | `/plugin install go-lsp@claude-plugins-official` |
| Rust | `/plugin install rust-lsp@claude-plugins-official` |

These require the language's server binary on each machine, and installing from the official marketplace needs network access to GitHub. To enable for the whole repo rather than per-user, add to the `enabledPlugins` project setting. Surface only the languages actually detected in Phase 1.

## SessionStart hook registration

Register the bundled hook script (see `templates/sessionstart-hook.sh`) so its stdout is added to Claude's context before the first prompt. Merge into the existing `hooks` block; don't replace sibling hooks.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/disclosure-context.sh" }
        ]
      }
    ]
  }
}
```

The script receives the hook input (including the launch directory) and prints the matching recommendation from a committed path→context map. Keep it fast and side-effect-free — it runs on every session start.
