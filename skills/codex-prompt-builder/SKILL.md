---
name: codex-prompt-builder
description: Use when a user asks to create, refine, convert, or hand off a Codex prompt from session context, rough requirements, bug reports, feature ideas, implementation plans, code review requests, or task notes.
---

# Codex Prompt Builder

## Purpose

Turn available task context into a copy-ready Codex prompt. Infer from the current session or supplied text first, ask only for missing high-impact details, then output the prompt in the required four-section shape.

## Required Output Shape

Always produce the final prompt with these headings, in this order:

```text
Goal:
Context:
Constraints:
Done when:
```

Return only the copy-ready prompt unless the user explicitly asks for rationale, variants, or a critique.

## Workflow

1. Identify the input source:
   - Use explicit user-provided prompt text as primary source material.
   - If no prompt text is provided, use the current session context.
   - If both exist, use the explicit prompt as the task and session context as supporting detail.
2. Extract the four fields:
   - `Goal`: the concrete change, investigation, review, or deliverable Codex should complete.
   - `Context`: relevant files, folders, docs, examples, commands, errors, PRs, screenshots, or prior decisions. Preserve `@` mentions and exact paths when provided.
   - `Constraints`: architecture rules, conventions, safety requirements, style preferences, tooling, non-goals, and things Codex must avoid.
   - `Done when`: observable completion criteria such as tests passing, behavior changing, docs updated, errors no longer reproducing, or a review report produced.
3. Gap-check before writing:
   - Ask about missing details only when they materially change execution quality, scope, safety, or verification.
   - Do not ask for information already inferable from local context or the user's prompt.
   - If the answer is useful but not essential, make a conservative assumption and include it in the prompt.
4. Produce a polished prompt:
   - Make it specific enough for another Codex session to act without guessing.
   - Keep it concise and implementation-oriented.
   - Do not invent files, tests, APIs, repo state, product requirements, or deadlines.

## Asking Questions

Use AskQuestion/request_user_input when available. Ask 1-3 focused questions at a time, using concrete options when possible. If that tool is unavailable, ask concise plain-text questions.

Ask only for high-impact gaps:

- Missing goal: what Codex should change, build, debug, review, or plan.
- Missing scope: target files, folders, subsystem, platform, or repo area.
- Missing constraints: style, architecture, safety, compatibility, or non-goals.
- Missing success criteria: tests, commands, behavior, output format, acceptance checks.
- Missing risk choice: tradeoffs that would lead to meaningfully different implementation.

Do not ask:

- For preferences that are already stated.
- For repo facts that can be discovered by inspection.
- For exhaustive detail when a reasonable default will make the prompt usable.

## Defaults

Use these defaults when the user does not specify otherwise:

- Codex should inspect the relevant codebase before editing.
- Codex should follow existing project patterns and avoid unrelated refactors.
- Codex should preserve unrelated user changes in the worktree.
- Codex should verify with the narrowest meaningful tests or checks available.
- Codex should report any verification it could not run.

## Use Case Shaping

- Feature implementation: include user-facing behavior, likely entry points, design/API constraints, and acceptance tests.
- Bug fix: include symptoms, reproduction steps, logs/errors, suspected areas, and the command or behavior that proves the fix.
- Refactor: include the reason, boundaries, compatibility expectations, and tests that must remain green.
- Code review: include review focus, changed files or PR context, severity expectations, and desired report format.
- Research or planning: include decision to make, sources or repo areas to inspect, constraints, and expected plan format.
- UI/frontend: include target audience, interaction states, responsive requirements, accessibility expectations, and visual constraints.

## Quality Bar

The final prompt should be:

- Actionable: Codex can immediately start.
- Bounded: scope and non-goals are clear.
- Grounded: context is factual or clearly marked as assumed.
- Verifiable: `Done when` names concrete checks or outcomes.
- Portable: it can be pasted into a fresh Codex session without relying on hidden conversation state.
