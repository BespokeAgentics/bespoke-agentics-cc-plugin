---
name: bespokeagentics:pi-customize-harness
description: Customize a Pi harness through settings, context files, or extensions
argument-hint: <customization-task>
allowed-tools: Skill(pi-assistant)
---

Use the pi-assistant skill to customize the current Pi harness for: $ARGUMENTS

Inspect the local Pi setup first, then choose the smallest effective surface among `AGENTS.md`, `SYSTEM.md`, `APPEND_SYSTEM.md`, `.pi/settings.json`, skills, prompt templates, extensions, or packages.
