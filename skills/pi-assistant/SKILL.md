---
name: pi-assistant
description: "Customize the pi.dev coding agent harness — settings, AGENTS.md, skills, extensions, Pi Packages. Use for Pi (`@mariozechner/pi-coding-agent`) setup, debugging, or package install."
---

# Pi Assistant

## Overview

Use this skill to work with Pi through its supported customization surfaces instead of forking internals by default. Inspect the current setup, choose the smallest effective extension point, then implement or recommend the change with explicit paths, scope, and install commands.

## Task Routing

- Read [references/pi-harness.md](references/pi-harness.md) first for harness behavior, context files, settings, modes, and built-in customization surfaces.
- Read [references/pi-extensions.md](references/pi-extensions.md) when the task involves custom slash commands, custom tools, lifecycle hooks, UI, event interception, or `pi.registerCommand(...)`.
- Read [references/pi-skills.md](references/pi-skills.md) when the task involves Pi skills, skill discovery, `/skill:name`, Agent Skills frontmatter, or reusing Claude/Codex skills inside Pi.
- Read [references/pi-packages.md](references/pi-packages.md) when the task involves package discovery, package structure, install/remove/update flows, `pi install`, package manifests, or resources shared through npm, git, or local paths.
- Run `python3 skills/pi-assistant/scripts/search_pi_packages.py "<query>"` when the user wants to discover packages. Prefer this over manually trawling the gallery; browse official docs or package pages only when you need README-level detail or verification.

## Workflow

1. Inspect the local Pi surface area before changing anything:
   - project: `.pi/`, `.agents/skills/`, `.agents/prompts/`, `.agents/themes/`, `AGENTS.md`, `CLAUDE.md`
   - global: `~/.pi/agent/`, `~/.agents/skills/`
   - package manifests: `package.json`, `.pi/settings.json`, `~/.pi/agent/settings.json`
2. Classify the request:
   - harness customization
   - extension or slash-command authoring
   - skill authoring
   - package discovery or install
   - package authoring
   - setup audit or debugging
3. Make the smallest change that uses Pi's supported extension points. Prefer settings, context files, skills, extensions, or packages over patching harness internals.
4. Validate after changes:
   - re-read changed files
   - recommend or run `/reload`, `pi list`, `pi install`, or `pi update` when appropriate
   - confirm paths and scope explicitly: global vs project-local

## Harness Customization

- Use `AGENTS.md` or `CLAUDE.md` for shared project instructions Pi should load from the current directory and its ancestors.
- Use `.pi/SYSTEM.md` or `~/.pi/agent/SYSTEM.md` to replace the default system prompt.
- Use `APPEND_SYSTEM.md` variants when the user wants to extend Pi's default prompt instead of replacing it.
- Use prompt templates for reusable prompt snippets, skills for reusable workflows, and extensions when Pi behavior or tools must change.
- Prefer project-local `.pi/` configuration when the behavior should travel with the repo. Prefer `~/.pi/agent/` only for personal defaults.

## Extensions and Slash Commands

- Pi slash commands come from built-in commands, extension `pi.registerCommand(...)`, prompt templates, and `/skill:name`.
- Reach for an extension when the user needs any of these:
  - a true custom slash command
  - custom tools callable by the model
  - event interception or permission gates
  - custom UI or persistent session state
- Keep extensions project-local in `.pi/extensions/` unless the behavior should be global.
- Extensions are TypeScript modules loaded by `jiti`; they can import npm dependencies from a nearby `package.json`.
- When implementing commands, follow the current Pi extension API rather than inventing a separate command format.

## Skills

- Pi loads skills from `.pi/skills/`, `.agents/skills/`, `~/.pi/agent/skills/`, `~/.agents/skills/`, package `skills/` directories, explicit `settings.json` entries, or `--skill`.
- Pi can reuse Claude/Codex skill directories through settings. When that is simpler than rewriting a skill, add the external path to Pi settings.
- Keep skill metadata specific so Pi can load the right skill without needing `/skill:name` every time.
- Use `/skill:name` when the user wants to force a skill or when automatic loading is unreliable.

## Pi Packages

- Package discovery:
  - `python3 skills/pi-assistant/scripts/search_pi_packages.py "<query>"` for quick search
  - `pi.dev/packages` for gallery browsing
  - npm search by the `pi-package` keyword for verification
- Install sources:
  - `pi install npm:<pkg>`
  - `pi install git:github.com/user/repo@ref`
  - `pi install https://github.com/user/repo@ref`
  - `pi install /abs/path` or `./relative/path`
- Scope:
  - default or global: `~/.pi/agent/settings.json`
  - project-local: `pi install -l ...` writes to `.pi/settings.json`
- Prefer project installs for repo-specific workflows and team-shared behavior. Prefer global installs for personal utilities.

## Package Authoring

- A Pi package can expose `extensions`, `skills`, `prompts`, and `themes` from `package.json` under `pi`, or via conventional directories.
- Include the `pi-package` keyword when the goal is discoverability in the Pi gallery.
- Keep runtime dependencies in `dependencies`.
- If you depend on Pi core packages in an extension package, list them in `peerDependencies` with `"*"` and do not bundle them.
- Prefer conventional directories unless the user needs filtered or nonstandard paths.

## Implementation Heuristics

- If the user wants to change how Pi behaves, start with harness files and settings, then escalate to extensions only if configuration is not enough.
- If the user wants a command in Pi, implement an extension command, a prompt template, or a skill command as appropriate.
- If the user wants shareable customization, package it as a Pi package rather than a pile of undocumented local files.
- If the user wants a package recommendation, search first, then summarize best fits, tradeoffs, maintenance signals, and exact install commands.
- If the user wants to customize harness internals directly, explain the supported extension point first and patch internals only when they explicitly want a fork.

## Quick Commands

```bash
# Search Pi packages by npm keyword
python3 skills/pi-assistant/scripts/search_pi_packages.py "browser automation"

# Install globally
pi install npm:some-pi-package

# Install for the current repo
pi install -l npm:some-pi-package

# Try an extension package without persisting it
pi -e npm:@scope/pi-extension
```

## Output Expectations

- Always name the exact files or settings you changed.
- When recommending package installs, include the exact `pi install` command and whether it is global or project-local.
- When building Pi resources, preserve upstream Pi conventions so the result works with `/reload`, startup auto-discovery, and shared settings.
