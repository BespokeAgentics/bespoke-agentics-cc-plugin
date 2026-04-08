---
name: bespokeagentics:pi-build-package
description: Build or update a shareable Pi package with conventional resources
argument-hint: <package-task>
allowed-tools: Skill(pi-assistant)
---

Use the pi-assistant skill to build or update a shareable Pi package for: $ARGUMENTS

Prefer conventional `extensions/`, `skills/`, `prompts/`, and `themes/` directories unless the package needs a custom `pi` manifest. Include the `pi-package` keyword when discoverability in the package gallery matters.
