# Claude Code Hook Spec — SessionStart, SessionEnd, Stop

Reference notes the skill agent reads on demand. This is the contract between Claude Code and your hook scripts.

## Configuration Shape

Hooks live in `.claude/settings.json`, `.claude/settings.local.json`, or `~/.claude/settings.json`. The merge order is: enterprise → user → project → local.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/start-wiki-context.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/stop-wiki-log.sh",
            "timeout": 15
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/stop-summary.py",
            "timeout": 45
          }
        ]
      }
    ]
  }
}
```

## Event Reference

### SessionStart

Fires when Claude Code starts a brand-new session OR resumes one. Matchers let you discriminate:

| Matcher | When it fires |
|---------|---------------|
| `startup` | Fresh session |
| `resume` | `claude --resume`, `--continue`, or `/resume` |
| `clear` | After `/clear` |
| `compact` | After a context compaction |

Use this hook to **inject context**: read files, query APIs, return text that becomes part of the system prompt preamble.

Default timeout: **60s**. Long fetches should bump this (`"timeout": 120`) but keep it reasonable — every session start pays this cost.

### SessionEnd

Fires when the session terminates (user closes the CLI, kills the process, or the agent finishes a one-shot run). Cannot block termination. Use for cleanup, final log writes, notifications.

Default timeout: **60s**.

### Stop

Fires when **Claude finishes responding** (every assistant turn). NOT once per session — once per turn. Use for per-turn audits, final-message annotations, or short status updates.

A Stop hook CAN block continuation by returning JSON with `"decision": "block"`. Use sparingly.

Default timeout: **60s**.

## Input — what the hook receives

Hooks receive a JSON object on **stdin**. Read it with `cat` (bash) or `json.load(sys.stdin)` (python).

Common fields across all three events:

```json
{
  "session_id": "abc-123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/Users/me/my-project",
  "hook_event_name": "SessionStart"
}
```

Event-specific extras:

| Event | Extra fields |
|-------|--------------|
| `SessionStart` | `source` ("startup", "resume", "clear", "compact") |
| `SessionEnd` | `reason` ("user_exit", "timeout", "error") |
| `Stop` | `stop_hook_active` (boolean — true if another stop hook fired this turn) |

## Output — what Claude Code accepts back

Two channels: **exit code** and **stdout**.

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success. stdout is parsed for JSON. If stdout is plain text on SessionStart, the text is appended as `additionalContext`. |
| `2` | Blocking error. stderr is shown to the user. Only meaningful for Stop and PreToolUse. |
| Any other non-zero | Non-blocking error. stderr is logged but the session continues. |

### Stdout — Plain Text (SessionStart only)

If a SessionStart hook prints plain text to stdout and exits 0, the text is **appended to Claude's context** as `additionalContext`. This is the simplest way to inject context.

```bash
echo "## Recent commits"
git log --oneline -10
exit 0
```

### Stdout — JSON

For richer control, print a JSON object. Recognized fields:

```json
{
  "continue": true,
  "stopReason": "optional message when continue=false",
  "suppressOutput": false,
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "## Confluence — Latest spec\n\n…"
  }
}
```

Per-event variants:

| Event | Use |
|-------|-----|
| `SessionStart` | Put context into `hookSpecificOutput.additionalContext` |
| `SessionEnd` | Honored fields: `continue`, `suppressOutput`. No `additionalContext` (session is ending) |
| `Stop` | `decision: "block"` + `reason: "…"` will make Claude continue instead of stopping. Most stop hooks ignore this. |

## Multiple Hooks Per Event

The `hooks` array is a list — Claude Code runs them in order. Each may have its own `matcher` (for SessionStart), command, and timeout. Their outputs are concatenated.

If you have ten SessionStart hooks each printing 2KB of context, you're spending 20KB of every session's context window before the user types anything. Be deliberate.

## Environment

Hook scripts inherit the environment of the Claude Code process. Standard practice:

- Reference secrets via env vars, not inline.
- Export `CLAUDE_PROJECT_DIR` upstream if you want a stable repo root inside the script.
- Use `cwd` from the input JSON as the source of truth for the working directory.
