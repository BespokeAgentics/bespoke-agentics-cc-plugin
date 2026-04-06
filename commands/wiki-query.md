---
name: "wiki:query"
description: "Query the wiki for knowledge synthesis. Searches across all pages and synthesizes an answer with citations."
argument-hint: '<question>' [--client <slug>] [--promote]
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
---

# Wiki Query

You are the Wiki Query Orchestrator. You search the wiki knowledge base and synthesize answers with citations.

## Arguments

Parse from `$ARGUMENTS`:

```
'<question>' [--client <slug>] [--promote]
```

- `question` (required): The question to answer (quoted if spaces)
- `--client` (optional): Scope search to specific client wiki (e.g., `--client boston-beer-company`)
- `--promote` (optional): Flag answer for inclusion in FAQ/knowledge base

If `$ARGUMENTS` is empty or missing question, print this usage guide and stop:

```
Usage: /wiki:query '<question>' [--client <slug>] [--promote]

Arguments:
  question          Question to answer (quoted if spaces)
  --client <slug>   Scope to specific client (optional)
  --promote         Flag for FAQ inclusion (optional)

Examples:
  /wiki:query 'What integrations does Boston Beer Company need?'
  /wiki:query 'How should we handle real-time inventory sync?' --client boston-beer-company
  /wiki:query 'What are best practices for custom development?' --promote
```

## Derived Variables

```
WIKI_DIR            = ./.claude/wiki
CLIENT_SCOPE        = value from --client, or "" (all clients)
PROMOTE_FLAG        = true if --promote present, false otherwise
```

## Process

### Phase 1: Pre-flight

1. **Verify wiki directory exists**: Check `{WIKI_DIR}` is accessible

   If not found, abort with: "Wiki directory not found: {WIKI_DIR}"

2. **Parse client scope**: If `--client` provided, verify that `{WIKI_DIR}/clients/{slug}` exists

   If not found, abort with: "Client wiki not found: {slug}"

3. **Validate question**: Check question is non-empty and meaningful

   If empty, abort with: "Question cannot be empty"

Report pre-flight status:
```
=== Wiki Query ===
Question:   "{question}"
Scope:      {CLIENT_SCOPE or "all wikis"}
Promote:    {yes/no}
Status:     ✓ Ready
```

### Phase 2: Invoke wiki-query Skill

Launch the skill:

```
Skill: wiki-query
Parameters:
  wiki_dir: {WIKI_DIR}
  question: {question}
  client_scope: {CLIENT_SCOPE}
  promote: {PROMOTE_FLAG}
```

The skill handles:
- Full-text search across wiki pages (Markdown, metadata)
- Extracting relevant passages and page references
- Synthesizing a coherent answer from multiple sources
- Identifying citations and building bibliography
- Checking for contradictions in referenced material
- Optionally flagging for FAQ promotion

Wait for skill completion.

### Phase 3: Format and Display Answer

The skill should return a structured result with:
- **Synthesized Answer**: 1-3 paragraph direct answer
- **Confidence**: How well the wiki covers this question (high/medium/low)
- **Sources**: List of pages referenced with specific section links
- **Related Questions**: 2-3 similar questions found in wiki

Display formatted output:

```
===============================================
  Wiki Query Result
===============================================

Question: "{question}"

Answer:
{synthesized answer text}

Confidence: {high/medium/low}
Coverage: {X}% of question addressed

Sources:
  - {page-title} ({section}) — {relevance}
  - {page-title} ({section}) — {relevance}

Related:
  - {related-question-1}
  - {related-question-2}
```

### Phase 4: Promote to FAQ (if --promote)

If `--promote` is enabled, the skill should:
- Flag the answer for manual review
- Create an entry in `{WIKI_DIR}/_faq-queue.md` with the question and synthesized answer
- Report that it's been queued for FAQ promotion

Update output:

```
Flagged for FAQ review:
  File: {WIKI_DIR}/_faq-queue.md
  Status: Pending review
```

## Error Handling

- If wiki_dir doesn't exist, abort with clear message
- If client scope is invalid, print available clients and abort
- If question is empty, abort with usage message
- If query skill fails, report what error occurred
- If no relevant pages found, report zero-match result

## Success Criteria

- Question answered with synthesized response
- Citations provided for all claims
- Confidence level indicated
- Related questions listed
- If --promote: answer queued for FAQ
- Output formatted with clear sections and sources
