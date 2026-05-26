# Hook Security & Safety

Hooks run with the user's full shell privileges. A misconfigured hook can leak secrets, slow every session to a crawl, or stomp the wiki. These are the guardrails.

## Secrets

**Never** inline a token in a script committed to git. Use env vars and document them in the design doc.

```bash
# BAD
curl -H "Authorization: Bearer sk-abc123..." https://api.example.com

# GOOD
: "${MY_API_TOKEN:?MY_API_TOKEN must be set}"
curl -H "Authorization: Bearer $MY_API_TOKEN" https://api.example.com
```

The `:?` pattern aborts the script with a clear error if the var is missing, while still allowing the hook to exit 0 (it errored, but didn't pretend to succeed). For graceful degrade, use:

```bash
if [ -z "${MY_API_TOKEN:-}" ]; then
  echo "warn: MY_API_TOKEN not set, skipping" >&2
  exit 0
fi
```

Project-scope hooks (in `.claude/settings.json`) get committed. Local-scope hooks (in `.claude/settings.local.json`) do not. If a hook references a personal token, prefer local scope.

## Timeouts

Always set explicit timeouts in `settings.json`. Don't rely on the 60s default for anything network-bound — set 30s or 45s so a stuck request can't tank your session.

For network calls in the script itself, add another layer of timeout:

```bash
# bash
curl --max-time 10 ...

# python
requests.get(url, timeout=10)
```

Defense in depth.

## Idempotency

Stop hooks fire on every assistant turn — many times per session. If your stop hook appends to a log, it will produce duplicate entries unless you guard against it.

Strategies:

1. **Daily lock file:** `if [ -f .claude/hooks/.locked-$(date +%F) ]; then exit 0; fi`
2. **Marker line check:** Read the last line of the log; skip if the timestamp matches.
3. **Use SessionEnd instead of Stop** when you only want once-per-session behavior.

## Output Volume

Anything a SessionStart hook prints becomes `additionalContext` — it goes into the prompt. If you dump 50KB of git log into every session, you've burned tens of thousands of tokens before the user types a word.

Rule of thumb: keep `additionalContext` under 4KB per hook. Truncate liberally. Summarize via `awk`, `head`, or a quick LLM call rather than dumping raw output.

## Failure Mode

The single most important rule: **hooks fail open**. A failed Confluence fetch must not prevent Claude from starting.

```bash
fetch_confluence || {
  echo "warn: confluence fetch failed, continuing without it" >&2
  exit 0
}
```

`exit 0` even on failure. Print to stderr so the user is aware, but never block the session start.

## Path Safety

Use absolute paths from the hook input or `CLAUDE_PROJECT_DIR`. Do not assume the script's CWD.

```bash
# Read input JSON to get the canonical project root
INPUT=$(cat)
PROJECT_DIR=$(echo "$INPUT" | jq -r '.cwd')
cd "$PROJECT_DIR" || exit 0
```

## Avoid External Side Effects on Start

SessionStart hooks fire frequently — every fresh session, every `/clear`, every resume. Do not:

- Send Slack messages or emails from SessionStart.
- Create Confluence pages from SessionStart.
- Modify code from SessionStart.

Those belong in Stop / SessionEnd. SessionStart should be **read-only**.

## Audit Trail

If a hook does anything destructive (writes a page, posts to a channel, modifies code), log it. The bespoke-agentics convention is `wiki/_log.md` — every hook-driven action gets a row.

## Testing a Hook

Always test in isolation before installing:

```bash
echo '{"session_id":"test","cwd":"'$(pwd)'","hook_event_name":"SessionStart","source":"startup"}' | .claude/hooks/start-wiki-context.sh
```

If it doesn't print the right context or returns non-zero, fix it before adding to `settings.json`.
