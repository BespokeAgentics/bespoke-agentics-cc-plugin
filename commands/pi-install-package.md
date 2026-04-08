---
name: bespokeagentics:pi-install-package
description: Install a Pi package with the right source and scope
argument-hint: <package-source-or-name> [--local]
allowed-tools: Skill(pi-assistant)
---

Use the pi-assistant skill to install or stage a Pi package for: $ARGUMENTS

Determine whether the package should be global or project-local, prefer exact `pi install` commands, and explain which settings file or Pi-managed directory the change will affect.
