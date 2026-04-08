# Pi Skills Reference

## Contents

- Skill locations and discovery
- Skill structure
- Skill commands
- Reusing Codex or Claude skills
- Skill authoring checklist

## Skill Locations and Discovery

Pi loads skills from these locations:

- `~/.pi/agent/skills/`
- `~/.agents/skills/`
- `.pi/skills/`
- `.agents/skills/` in the current directory and ancestor directories
- package `skills/` directories or `pi.skills` manifest entries
- explicit `skills` entries in settings
- `--skill <path>`

Discovery rules worth remembering:

- directories containing `SKILL.md` are discovered recursively
- root `.md` files are discovered in `~/.pi/agent/skills/` and `.pi/skills/`
- root `.md` files are ignored in `~/.agents/skills/` and project `.agents/skills/`

## Skill Structure

A Pi skill is a directory containing `SKILL.md`. Optional bundled resources can include:

- `scripts/`
- `references/`
- `assets/`

Frontmatter essentials:

- `name`
- `description`

Pi follows the Agent Skills standard and is lenient about many violations, but a missing description prevents loading.

## Skill Commands

Pi exposes skills as `/skill:name` commands.

Examples:

```bash
/skill:brave-search
/skill:pdf-tools extract
```

Use `/skill:name` when:

- you want to force a skill to load
- auto-discovery is too broad or unreliable
- the user explicitly wants a particular skill

## Reusing Codex or Claude Skills

Pi can load skills from other harnesses through settings.

Examples:

```json
{
  "skills": [
    "~/.claude/skills",
    "~/.codex/skills"
  ]
}
```

Project-local example:

```json
{
  "skills": ["../.claude/skills"]
}
```

This is often simpler than rewriting an existing skill if the original structure already matches Pi's expectations.

## Skill Authoring Checklist

1. Keep the description specific enough to trigger correctly.
2. Put detailed docs in `references/` instead of bloating `SKILL.md`.
3. Use relative paths from the skill directory.
4. Keep scripts executable and self-contained.
5. Validate by loading the skill in Pi or forcing it with `/skill:name`.
