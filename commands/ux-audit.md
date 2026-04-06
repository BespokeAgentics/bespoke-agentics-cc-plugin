---
description: Run a full UX audit on code, screenshots, or video using Nielsen heuristics and Norman principles
argument-hint: <path-or-description>
allowed-tools: Skill(ux-audit), Read, Glob, Grep, Bash, Write, Agent
---

Invoke the ux-audit skill to perform a comprehensive UX audit.

Target: $ARGUMENTS

If no target is specified, scan the current working directory for front-end code files (.jsx, .tsx, .vue, .html, .css) and any uploaded screenshots, GIFs, or videos. Ask the user what to audit if nothing is found.

Run the full pipeline: determine input type, analyze against all heuristics and Norman principles, and generate the HTML report.
