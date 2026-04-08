---
name: bespokeagentics:pi-build-extension
description: Build or update a Pi TypeScript extension and its slash commands
argument-hint: <extension-task>
allowed-tools: Skill(pi-assistant)
---

Use the pi-assistant skill to build or update a Pi TypeScript extension for: $ARGUMENTS

Prefer `.pi/extensions/` for project-local behavior unless the request is explicitly global. Follow the current Pi extension API, including `pi.registerCommand(...)` for slash commands, and add a nearby `package.json` only when dependencies are required.
