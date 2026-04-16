# Upstream Glean Claude Code Skills

The `gleanwork/glean-agent-toolkit` repo ships two Claude Code skills that document the SDK in depth. This skill (`glean-agent-toolkit`) deliberately does **not** duplicate them — instead, it offers to install them and routes deep SDK questions to them.

> Verified against `glean-agent-toolkit` v0.5.0.

## The two upstream skills

| Skill | Path on GitHub | Use for |
|-------|----------------|---------|
| `glean-agent-toolkit-guide` | `skills/glean-agent-toolkit-guide/` | "How do I use the toolkit?" — install, env vars, the 9 built-in tools, all 4 adapters, `GleanContext`, `get_tools()` |
| `glean-agent-toolkit-builder` | `skills/glean-agent-toolkit-builder/` | "How do I create a new tool?" — `@tool_spec` decorator, Pydantic schema generation, `run_with_error_handling`, two implementation patterns, registration, testing |

Repo: <https://github.com/gleanwork/glean-agent-toolkit>

## Install (recommended: shallow clone + symlink)

Claude Code reads skills from `~/.claude/skills/`. The simplest reliable install for skills published in a subfolder of an upstream repo is a shallow clone + per-skill symlink:

```bash
# One-time clone (or `git pull` if you already have it)
mkdir -p ~/.claude/_external && cd ~/.claude/_external
[ -d glean-agent-toolkit ] || git clone --depth 1 https://github.com/gleanwork/glean-agent-toolkit.git
cd glean-agent-toolkit && git pull --ff-only

# Symlink each skill into the user's skills directory
mkdir -p ~/.claude/skills
ln -sfn "$PWD/skills/glean-agent-toolkit-guide" ~/.claude/skills/glean-agent-toolkit-guide
ln -sfn "$PWD/skills/glean-agent-toolkit-builder" ~/.claude/skills/glean-agent-toolkit-builder
```

Restart Claude Code. The skills should now appear in the skills list.

## Install (alternative: copy)

If symlinks are problematic on the user's system (e.g. some Windows setups):

```bash
mkdir -p ~/.claude/skills/glean-agent-toolkit-guide ~/.claude/skills/glean-agent-toolkit-builder
curl -fsSL https://raw.githubusercontent.com/gleanwork/glean-agent-toolkit/main/skills/glean-agent-toolkit-guide/SKILL.md \
  -o ~/.claude/skills/glean-agent-toolkit-guide/SKILL.md
curl -fsSL https://raw.githubusercontent.com/gleanwork/glean-agent-toolkit/main/skills/glean-agent-toolkit-builder/SKILL.md \
  -o ~/.claude/skills/glean-agent-toolkit-builder/SKILL.md
```

This pins to whatever main is at fetch time; re-run periodically to refresh.

## When to use upstream vs this skill

| Situation | Use |
|-----------|-----|
| "What does `@tool_spec` do?" | `glean-agent-toolkit-builder` |
| "Which built-in tools ship with the toolkit?" | `glean-agent-toolkit-guide` |
| "How do I adapt a tool to LangChain?" | `glean-agent-toolkit-guide` |
| "Scaffold me a new project" | This skill (`/glean:init`) |
| "Add a new custom tool to my project" | This skill (`/glean:add-tool`) — appends a stub matching the upstream patterns |
| "Wire LangChain into an existing project" | This skill (`/glean:add-adapter`) |
| "Why is my GLEAN_API_TOKEN being rejected?" | This skill (`/glean:doctor`) |

## Verifying install

```bash
ls -la ~/.claude/skills/ | grep glean
```

Expect three entries: `glean-agent-toolkit-guide`, `glean-agent-toolkit-builder`, and (if this plugin is symlinked) `glean-agent-toolkit`.
