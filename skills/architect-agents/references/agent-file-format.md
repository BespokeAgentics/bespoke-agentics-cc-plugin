# Agent File Format Reference

Quality rules and format requirements for generated `.claude/agents/*.md` files.

## YAML Frontmatter (required)

```yaml
---
name: {kebab-case-name}
description: {1-2 sentences. Include trigger phrases for when this agent should be proactively dispatched. End with "Use proactively for any {domain} work."}
tools: {comma-separated tool list}
model: {sonnet|opus}
---
```

**Field rules:**
- `name`: Must be kebab-case. Must match the filename (without `.md`).
- `description`: Must describe expertise AND include dispatch triggers. Example: "Expert React engineer for the portal app. Use when building pages, components, or tests in the portal. Specializes in React 18, Vitest, and MUI. Use proactively for any portal work."
- `tools`: Implementation agents get `Read, Write, Edit, Bash, Grep, Glob`. Validation agents and orchestrators get `Read, Bash, Grep, Glob` (no Write, no Edit).
- `model`: `sonnet` for implementation, `opus` for validation/orchestration (unless overridden).

## Required XML Sections

Every agent file MUST have these sections after the frontmatter:

### `<role>` (required)

```xml
<role>
You are a senior {specialization} engineer specializing in {domain}. You build {what they build} for {project context}.

Your working directory is: `{ABSOLUTE_PATH}`
You own: {list of owned paths}
</role>
```

**Rules:**
- Working directory MUST be an absolute path (e.g., `/Users/name/project/`)
- Never use `~` or relative paths
- "You own:" lists the specific directories this agent is responsible for

### `<constraints>` (required, minimum 5)

```xml
<constraints>
- **ALWAYS read existing code first.** Check {paths} before creating anything new.
- **NEVER {anti-pattern}.** {explanation of why}.
- **ALWAYS {required practice}.** {explanation}.
- **ALWAYS write tests** using {test framework} for every {testable unit}.
- Run {validation commands} before reporting completion.
</constraints>
```

**Rules:**
- Minimum 5 constraints
- Use **NEVER** and **ALWAYS** bold formatting
- First constraint is always "read existing code first" with specific paths
- Last constraint is always "run validation before reporting"
- Middle constraints come from: CLAUDE.md rules, AGENTS.md guidelines, framework-specific anti-patterns, domain-specific requirements
- Be specific: "NEVER use localStorage" not "NEVER use bad patterns"

### `<architecture>` (required)

```xml
<architecture>
**File Structure**

{actual directory tree from codebase — NOT generic/invented}

**Key Patterns**

{framework-specific patterns with code examples from the actual project}
</architecture>
```

**Rules:**
- File structure must be from the actual codebase (`ls` output), not invented
- Code examples must use the project's actual import patterns
- Include: naming conventions, file organization, state management approach
- If the project has documented patterns (in AGENTS.md etc.), include them here

### `<testing>` (required if project has tests)

```xml
<testing>
{Test framework, runner, and conventions}

{Actual test example from the codebase — or a realistic example following existing patterns}
</testing>
```

**Rules:**
- Must name the actual test framework (Vitest, Jest, pytest, etc.)
- Must include an example test that follows the project's conventions
- Prefer copying a real test from the codebase over inventing one
- Include setup patterns (test utilities, fixtures, mocking approach)

### `<validation>` (required)

```xml
<validation>
Before reporting work as complete, run:

` ` `bash
cd {absolute_path}
{actual commands from package.json scripts}
` ` `

Fix all errors. Only report success after all commands pass.
</validation>
```

**Rules:**
- Commands must come from the project's package.json/manifest scripts
- Use absolute paths in `cd` commands
- Always include typecheck + test + lint (if all three exist)
- Never invent commands — if a project has no linter, don't add a lint command

### `<output_format>` (required)

```xml
<output_format>
When completing a task, report:
1. **Files created/modified** with paths
{domain-specific items}
</output_format>
```

**Rules:**
- Always starts with "Files created/modified"
- Add domain-specific items: test coverage, API endpoints, schema changes, etc.
- Always ends with "Known limitations or follow-up items"

## Anti-Patterns (never do these)

- Generic working directory: `/path/to/project/` instead of actual path
- Invented validation commands not in any manifest
- Copy-pasted constraints that don't apply to this project
- Empty or placeholder sections
- Code examples using generic import patterns instead of the project's actual patterns
- Missing WCAG/accessibility constraints for UI component agents
- Validation agents with Write/Edit tools
- Descriptions without trigger phrases for proactive dispatch
