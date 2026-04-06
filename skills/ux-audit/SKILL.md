---
name: ux-audit
description: >
  Perform a comprehensive UX audit using Nielsen's 10 Usability Heuristics and Don Norman's 6
  Design Principles. Use this skill whenever the user uploads a codebase, component files,
  screencasts (MP4 or GIF), screenshots, or user flow recordings for UX review. Also trigger
  when the user asks about usability problems, UX violations, design critique, heuristic
  evaluation, or wants to find UX issues in their product. Works on React, HTML/CSS,
  Vue, Angular, mobile UI code, or any front-end code. Produces a structured severity-rated
  report with specific fixes.
---

# UX Audit Skill

Performs dual-lens UX analysis: Nielsen heuristics identify _what_ is broken; Norman principles
diagnose _why_ it's broken and how to fix it structurally.

---

## Step 0 — Determine input type

Inspect what the user has provided and route accordingly. Multiple input types can be combined.

| Input                                                       | Route                                           |
| ----------------------------------------------------------- | ----------------------------------------------- |
| `.jsx`, `.tsx`, `.vue`, `.html`, `.css`, `.js`, `.ts` files | → Code Analysis                                 |
| `.gif` file                                                 | → GIF Analysis (Claude reads directly as image) |
| `.mp4`, `.mov`, `.webm` file                                | → Video Frame Extraction, then analysis         |
| Screenshots (`.png`, `.jpg`)                                | → Static Visual Analysis                        |
| Combination                                                 | → Run all applicable routes, merge findings     |

If no files are provided but the user describes a flow or UI, ask them to share files or screenshots
for higher-quality findings. You can still provide guidance from descriptions, but flag it as
lower-confidence.

---

## Step 1 — Code Analysis

Read `references/code-patterns.md` before starting code analysis.

### 1a. Collect files

- Ask for or scan uploaded files. Look in `/mnt/user-data/uploads/` for any uploaded content.
- For large codebases, prioritize: form components, modal/dialog components, error handling,
  navigation, loading states, and any component named with words like: `form`, `modal`,
  `dialog`, `error`, `loading`, `submit`, `confirm`, `alert`, `toast`, `nav`, `wizard`, `step`.

### 1b. Scan against heuristic patterns

For each file, check the full pattern list in `references/code-patterns.md`.
Flag every instance with:

- File name and line number
- Heuristic violated (H1–H10)
- Norman principle violated (N1–N6)
- Severity: Critical / High / Medium / Low (see severity guide below)
- The exact code causing the issue
- A specific code fix

### 1c. Severity guide

| Level        | Criteria                                                            |
| ------------ | ------------------------------------------------------------------- |
| **Critical** | Blocks task completion, causes data loss, or creates silent failure |
| **High**     | Causes significant confusion, extra steps, or frequent errors       |
| **Medium**   | Creates friction or violates conventions; user recovers with effort |
| **Low**      | Polish issue; minor inconsistency; advanced-user concern            |

---

## Step 2 — Screencast / GIF Analysis

### For GIF files

GIFs are readable as images. Analyze the animation sequence directly.
Look for: timing of feedback, presence/absence of loading states, error flows, modal behavior,
navigation clarity, and whether the system communicates what happened after each action.

### For MP4 / MOV / WEBM files

Extract frames using ffmpeg before analysis:

```bash
# Install if needed
which ffmpeg || apt-get install -y ffmpeg 2>/dev/null

# Extract 1 frame per second (adjust rate for longer videos)
ffmpeg -i /mnt/user-data/uploads/YOUR_FILE.mp4 \
  -vf "fps=1" \
  /home/claude/frames/frame_%04d.png \
  -hide_banner -loglevel error

# For longer videos, use fps=0.5 (one frame every 2 seconds)
# For short demos (<30s), use fps=2 for more detail
```

After extraction, read the frames sequentially and analyze as a user flow.

### Visual analysis checklist

Work through each of these as you review frames in sequence:

**Feedback & Status (H1, N3-Feedback)**

- [ ] Does every action produce visible feedback within ~100ms?
- [ ] Are loading/processing states shown for operations >500ms?
- [ ] Is success/failure communicated clearly after form submission?
- [ ] Does the URL or breadcrumb update to reflect navigation?

**Navigation & Wayfinding (H1, H6, N4-Mapping)**

- [ ] Can the user tell where they are at all times?
- [ ] Is there a clear path back to where they came from?
- [ ] Do labels in the nav match the page titles they lead to?

**Error States (H5, H9, N1-Affordances)**

- [ ] Are errors shown inline, near the field that caused them?
- [ ] Are error messages in plain language with a next step?
- [ ] Can the user recover without losing their progress?

**Controls & Affordances (H3, N1-Affordances, N2-Signifiers)**

- [ ] Do interactive elements look interactive?
- [ ] Is it obvious what each control does before clicking?
- [ ] Are destructive actions (delete, submit) distinguishable from safe ones?

**Cognitive Load (H6, H8, N4-Mapping, N6-Constraints)**

- [ ] Is the screen's primary action obvious?
- [ ] Is information density appropriate for the task?
- [ ] Are related controls grouped spatially?

**Flow & Exit Points (H3, H7)**

- [ ] Can the user cancel/undo at each step?
- [ ] Are keyboard shortcuts or accelerators available for power users?

---

## Step 3 — Generate Report

Read `references/report-format.md` before generating the report.

The report must be output as an HTML file (not markdown) for readability and shareability.
Save to `/mnt/user-data/outputs/ux-audit-report.html`.

The report structure:

1. **Executive Summary** — 3–5 sentences. Severity score, top 3 findings, overall UX health.
2. **Findings Table** — All issues sorted by severity (Critical first).
3. **Findings Detail** — Each finding expanded with: location, what the user experiences,
   which heuristic/principle, the fix, and a before/after code snippet where applicable.
4. **Opportunities** — Positive observations or quick wins not captured in violations.
5. **Methodology note** — What was analyzed (files, video length, frames reviewed).

---

## Step 4 — Calibration rules

Follow these rules to avoid false positives and over-reporting:

- **Don't flag what you can't see.** If a button might have a handler elsewhere, say "potentially
  missing feedback — verify handler at [location]" rather than reporting it as a confirmed violation.
- **Context matters.** An admin-only power tool has different expectations than a consumer onboarding
  flow. Ask the user about the audience if it's unclear.
- **Code patterns are proxies.** A missing `aria-label` is a probable H1/H7 violation; a present
  one doesn't guarantee the label is meaningful. Note the distinction.
- **Rate severity conservatively.** When in doubt between Critical and High, use High. Over-alarming
  dilutes the report's credibility.
- **One finding per root cause.** If 12 buttons are missing loading states, that's one High finding
  with 12 instances — not 12 separate findings.

---

## Reference files

| File                                 | When to read                                                           |
| ------------------------------------ | ---------------------------------------------------------------------- |
| `references/heuristics-reference.md` | When you need the full heuristic definitions and diagnostic questions  |
| `references/code-patterns.md`        | Before all code analysis — contains the full pattern detection library |
| `references/report-format.md`        | Before generating the HTML report                                      |
