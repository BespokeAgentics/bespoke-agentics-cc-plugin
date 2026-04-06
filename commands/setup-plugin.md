---
name: bespokeagentics:setup-plugin
description: Scaffold, optimize, and package a folder as a well-formed Claude Code plugin
argument-hint: <folder-path> [--namespace <prefix>] [--author <name>]
allowed-tools: Skill(setup-plugin), Read, Write, Edit, Bash, Grep, Glob, Agent
---

Invoke the setup-plugin skill to convert a project folder into a distributable Claude Code plugin.

Target folder: $ARGUMENTS

Scan the folder for existing `.claude/` directories, skills, commands, agents, hooks, and scripts. Present an inventory to the user, then restructure, optimize, generate metadata (plugin.json, marketplace.json), and produce a comprehensive README.

If the folder already has plugin structure, run in audit-and-optimize mode — fix frontmatter, descriptions, naming, and regenerate the README.
