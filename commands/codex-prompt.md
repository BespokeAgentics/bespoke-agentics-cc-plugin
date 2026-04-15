---
name: bespokeagentics:codex-prompt
description: Turn session context or a supplied task into a well-formed Codex prompt
argument-hint: [prompt-or-context]
allowed-tools: Skill(codex-prompt-builder)
---

Use the codex-prompt-builder skill to turn this into a copy-ready Codex prompt:

$ARGUMENTS

If `$ARGUMENTS` is empty, use the current session context as the source material. Produce only the final prompt with `Goal:`, `Context:`, `Constraints:`, and `Done when:` unless the user explicitly asks for additional explanation.
