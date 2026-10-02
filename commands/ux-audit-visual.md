---
name: ux-audit-visual
description: Audit screenshots, GIFs, or video recordings for UX issues (skip code analysis)
argument-hint: <path-to-image-or-video>
allowed-tools: Read, Bash, Write, Agent
disable-model-invocation: true
---

> **How this command loads its skill.** `ux-audit` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/ux-audit/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

Follow the ux-audit skill (loaded as described above), running only the Visual Analysis route (Step 2).

Target: $ARGUMENTS

Skip code analysis entirely. Analyze the provided screenshots, GIFs, or video files against the visual analysis checklist:

- Feedback & Status (H1, N3)
- Navigation & Wayfinding (H1, H6, N4)
- Error States (H5, H9, N1)
- Controls & Affordances (H3, N1, N2)
- Cognitive Load (H6, H8, N4, N6)
- Flow & Exit Points (H3, H7)

For video files, extract frames with ffmpeg before analysis. For GIFs, analyze directly as images.

Generate the HTML report with findings from visual analysis only.
