---
name: codex-prompt
description: Turn session context or a supplied task into a well-formed Codex prompt
argument-hint: [prompt-or-context]
allowed-tools: Read
disable-model-invocation: true
---

> **How this command loads its skill.** `codex-prompt-builder` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/codex-prompt-builder/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

Follow the codex-prompt-builder skill (loaded as described above) to turn this into a copy-ready Codex prompt:

$ARGUMENTS

If `$ARGUMENTS` is empty, use the current session context as the source material. Produce only the final prompt with `Goal:`, `Context:`, `Constraints:`, and `Done when:` unless the user explicitly asks for additional explanation.
