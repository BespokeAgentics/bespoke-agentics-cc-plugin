# Biome AI Guardrails — Rule Coverage Matrix

This matrix documents which rules are handled natively by Biome and which require the sidecar ESLint config.

## Native Biome Rules

These rules are enforced directly in `biome.json` and run extremely fast.

| Rule | Biome Rule Name | Category | Level |
|------|----------------|----------|-------|
| Cognitive complexity cap (≤ 10) | `noExcessiveCognitiveComplexity` | complexity | error |
| No forEach (use for...of/map) | `noForEach` | complexity | error |
| Prefer flatMap | `useFlatMap` | complexity | error |
| Simplified logic expressions | `useSimplifiedLogicExpression` | complexity | error |
| No unused variables | `noUnusedVariables` | correctness | error |
| No unused imports | `noUnusedImports` | correctness | error |
| Exhaustive React deps | `useExhaustiveDependencies` | correctness | error |
| No var keyword | `noVar` | style | error |
| Prefer const | `useConst` | style | error |
| Template literals | `useTemplate` | style | error |
| Shorthand assignment | `useShorthandAssign` | style | error |
| Single var declarator | `useSingleVarDeclarator` | style | error |
| Naming conventions | `useNamingConvention` | style | error |
| No console.log | `noConsoleLog` | suspicious | error |
| No explicit any | `noExplicitAny` | suspicious | error |
| Strict equality (===) | `noDoubleEquals` | suspicious | error |
| No implicit any let | `noImplicitAnyLet` | suspicious | error |
| No hardcoded secrets | `noSecrets` | nursery | warn |
| No magic numbers | `noMagicNumbers` | nursery | warn |

## ESLint Sidecar Rules

These rules require the `eslint.ai-guardrails.mjs` config because Biome does not have native equivalents.

| Rule | ESLint Rule | Plugin | Level |
|------|------------|--------|-------|
| No comments in code | `no-comments/disallowComments` | eslint-plugin-no-comments | error |
| Max 2 function parameters | `better-max-params/better-max-params` | eslint-plugin-better-max-params | error |
| Max 50 lines per function | `max-lines-per-function` | built-in | error |
| Max 250 lines per file | `max-lines` | built-in | error |
| No magic numbers (strict) | `no-magic-numbers` | built-in | error |
| Max nesting depth 4 | `max-depth` | built-in | error |
| Max 20 statements per function | `max-statements` | built-in | error |
| Max 1 class per file | `max-classes-per-file` | built-in | error |
| Min identifier length 2 | `id-length` | built-in | error |
| No direct process.env access | `no-restricted-syntax` | built-in | error |

## Why the Sidecar?

Biome is extremely fast and covers formatting + a strong set of correctness/style rules natively. However, the structural guardrails that are central to constraining AI-generated code (size limits, parameter counts, no-comments) are not yet available in Biome's stable rule set.

The sidecar ESLint config is intentionally minimal — it only covers the gap rules and relies on two plugins:
- `eslint-plugin-no-comments` — bans all comments to force self-documenting code
- `eslint-plugin-better-max-params` — limits function parameters to force typed parameter objects

All other sidecar rules use ESLint built-in rules that require no additional plugins.

## What Each Rule Enforces

### No Comments
Forces self-documenting code. AI loves redundant comments like `// downloads the file` above `downloadFile()`. Banning comments forces better naming and function extraction.

### Max 2 Function Parameters
Forces typed parameter objects with destructuring instead of long positional argument lists. Prevents unreadable call sites.

### Max 50 Lines Per Function
Forces extraction of helper functions. When a function hits 50 lines, it must be broken into smaller, single-purpose functions.

### Max 250 Lines Per File
Prevents god files. Forces proper module separation.

### No Magic Numbers
Eliminates unexplained literals like `10000` or `3`. Forces named constants, making intent explicit. Biome covers this at warn level; ESLint provides a stricter enforcement with configurable exceptions.

### Max Depth 4
Prevents deeply nested conditionals and loops. Forces early returns and extraction.

### Max 20 Statements
Caps function complexity at the statement level. Complements the line limit.

### Max 1 Class Per File
Forces single-responsibility modules.

### Min Identifier Length 2
Prevents cryptic single-letter variable names (except `_` for unused params).

### No process.env Access
Forces dependency injection for configuration. Prevents scattered env access throughout the codebase.
