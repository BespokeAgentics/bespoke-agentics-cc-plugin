---
name: ux-audit-visual
description: Audit screenshots, GIFs, or video recordings for UX issues (skip code analysis)
argument-hint: <path-to-image-or-video>
allowed-tools: Skill(ux-audit), Read, Bash, Write, Agent
---

Invoke the ux-audit skill, but ONLY run the Visual Analysis route (Step 2).

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
