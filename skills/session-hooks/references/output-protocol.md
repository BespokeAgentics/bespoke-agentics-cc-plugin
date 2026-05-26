# Hook Output Protocol — Cheat Sheet

The shortest possible guide to what to print and which exit code to return.

## SessionStart Hook

### Quick mode (plain text)

Exit 0. Anything you print to stdout is appended as `additionalContext`.

```bash
#!/bin/bash
echo "## Wiki summary"
cat wiki/_index.md
exit 0
```

### Structured mode (JSON)

Exit 0. Print a JSON object with `hookSpecificOutput.additionalContext`.

```python
import json, sys
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "## Open PRs\n\n- #142 Add login\n- #143 Fix bug"
    }
}))
sys.exit(0)
```

### Failure mode (graceful)

Don't crash. Print warning to stderr, empty stdout, exit 0.

```bash
if ! command -v gh >/dev/null; then
  echo "warn: gh CLI not installed, skipping PR fetch" >&2
  exit 0
fi
```

## Stop Hook

### Most common — just do cleanup, no output

```bash
#!/bin/bash
echo "$(date +%Y-%m-%d) session ended" >> wiki/_log.md
exit 0
```

### Block continuation (rare)

If a Stop hook decides Claude should keep going (e.g., tests still need to run), it can return:

```json
{
  "decision": "block",
  "reason": "Tests not yet run. Please run npm test before stopping."
}
```

Claude Code will continue the agent loop with `reason` as a new user message.

## SessionEnd Hook

Pure side-effect — flush logs, send notifications, sync to Confluence. No context injection. Always exit 0.

## Universal Failure Mode

For all three events:

| Situation | Exit code | stdout | stderr |
|-----------|-----------|--------|--------|
| Happy path | 0 | context or JSON | empty |
| Network down / token missing | 0 | empty | one-line warning |
| Bug in script | 0 | empty | traceback + "skipping" |
| Genuinely block the session | 2 (Stop only) | JSON with `decision:"block"` | reason |

**Rule of thumb:** Hooks fail open, not closed. A broken Confluence fetch should never prevent Claude from starting.

## Idempotency Pattern

Stop hooks often append to logs. Guard against multi-fire by checking a marker file:

```bash
LOCK=".claude/hooks/.last-log-$(date +%Y-%m-%d)"
if [ -f "$LOCK" ]; then exit 0; fi
touch "$LOCK"
echo "| $(date +%Y-%m-%d) | session | … |" >> wiki/_log.md
```

## Timeout Strategy

| Hook does... | Recommended timeout |
|--------------|---------------------|
| Reads a local file | 5s |
| Runs `git` commands | 10s |
| Calls a single MCP tool | 30s |
| Calls an external API (Confluence, GitHub) | 45s |
| Calls another LLM | 90s |

Always set an explicit timeout — don't rely on the default.
