---
description: "End-to-end client workflow analysis pipeline. Takes a video recording and produces comprehensive workflow documentation with application inventory, challenge mapping, and Claude/AI agent automation recommendations."
argument-hint: '<video-path>' '<client-name>' '<workflow-label>' [interval] [--skip-dedup] [--skip-transcribe] [--force]
allowed-tools: Skill(workflow-analyzer)
---

Invoke the workflow-analyzer skill for: $ARGUMENTS
