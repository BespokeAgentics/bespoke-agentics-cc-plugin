# Pattern Catalog — Creative SessionStart & Stop Hooks

A menu the skill agent can offer during the interview. Each pattern lists what it does, when it's worth it, and what it costs.

## SessionStart Patterns (load context in)

### 1. Wiki Pulse
**Reads:** `wiki/_index.md`, last 20 lines of `wiki/_log.md`.
**Injects:** A one-screen briefing on what the wiki currently contains and what changed recently.
**Best for:** Projects with an active wiki the team actually maintains. Costs almost nothing.
**Anti-pattern:** Don't do this if the wiki is stale — you'll bias Claude with old facts.

### 2. Confluence Spec Pin
**Reads:** A specific Confluence page or space (pinned via env var or config).
**Injects:** Title + body of the latest version, truncated to N tokens.
**Best for:** Active migration / implementation projects where one canonical spec changes often.
**Cost:** ~1 round-trip to Atlassian per session, 5–30s.
**Failure mode:** If Confluence is unreachable, skip silently.

### 3. Git Snapshot
**Reads:** `git status`, `git log --oneline -20`, current branch, files modified in the last 24h.
**Injects:** A compact "where you left off" block.
**Best for:** Solo devs, long-running feature branches, anyone who context-switches.
**Cost:** Negligible.

### 4. Open TODO Sweep
**Reads:** `grep -rn "TODO\|FIXME\|@claude:" src/`.
**Injects:** Top 10 with file:line links.
**Best for:** Codebases where TODOs are how the team communicates intent.
**Anti-pattern:** Don't do this if there are 4000 TODOs. Filter aggressively or pin specific tags.

### 5. Comment Inbox
**Reads:** Code comments tagged `@claude:` or `@bot:` — a custom protocol you invent.
**Injects:** "Notes left for you" — devs write comments addressed to Claude, knowing the next session will surface them.
**Best for:** Async pair programming with Claude. The dev tags spots they want Claude to look at next time.
**Variant:** Inverse — Stop hook *writes* `@claude:` notes back into the code based on what the session learned.

### 6. Recent Meeting Brief
**Reads:** N newest files in `meetings/`, `notes/`, or the wiki ingest output dir.
**Injects:** Compressed summary of the most recent meeting.
**Best for:** Teams using `/wiki:ingest-meeting` pipelines. Pairs with the bespoke-agentics meeting pipeline.

### 7. Open PR / Issue Pull
**Reads:** GitHub via `gh` CLI or GitHub MCP.
**Injects:** Your open PRs, your assigned issues, PRs awaiting your review.
**Best for:** Maintainers, code reviewers.
**Cost:** ~5s with `gh`, less with MCP.

### 8. CI Health
**Reads:** Latest GitHub Actions run, or Datadog/PagerDuty MCP if connected.
**Injects:** "Main is green/red. 2 open alerts." A 30-second early warning.
**Best for:** On-call rotations, deployment-heavy projects.

### 9. Second-Opinion AI Consultation
**Reads:** Nothing locally — calls a *different* model (GPT-5, Gemini-3) with a meta-prompt like "Here is the project's CLAUDE.md. What questions would you ask before starting work?"
**Injects:** The other model's framing.
**Best for:** Strategic / ambiguous work where another perspective is valuable.
**Cost:** API call + 10–30s.
**Cool factor:** High. The other AI essentially briefs Claude before you do.

### 10. Working Memory Resurrection
**Reads:** A persistent `notes.md` or `~/.claude/memory/{project}.md` that previous sessions wrote to.
**Injects:** Your evolving understanding of the project — facts, gotchas, decisions.
**Best for:** Long-running projects where you want Claude to "remember" between sessions.
**Pairs with:** A Stop hook that updates `notes.md`.

### 11. Stack Linter
**Reads:** Required env vars, installed CLI tools, language versions.
**Injects:** "Heads up: `gh` is missing, `node` is v18 not v20, `CONFLUENCE_TOKEN` is unset."
**Best for:** Teams that want predictable preflight.

### 12. Calendar Awareness
**Reads:** Today's calendar via Google Calendar MCP.
**Injects:** "You have a customer call in 30 min — keep session focused" or "Free until 5pm — okay to start deep work."
**Best for:** PM / customer-facing roles using Claude between meetings.

### 13. Inbox Pulse
**Reads:** Gmail / Outlook MCP — unread count + 3 most recent subjects from designated labels.
**Injects:** Quick scan of inbox state.
**Best for:** Communication-heavy workflows. Triages whether to start deep work.

### 14. Slack Briefing
**Reads:** Slack MCP — mentions in the last 24h, unreplied DMs.
**Injects:** Brief list.
**Best for:** Teams where context lives in Slack threads.

### 15. Recent Decision Log
**Reads:** `decisions/` or `docs/adr/` directories.
**Injects:** The most recent N ADRs.
**Best for:** Codebases with active architecture decision records.

---

## Stop / SessionEnd Patterns (capture context out)

### A. Wiki Log Line
**Writes:** A single row appended to `wiki/_log.md`: date, session ID, summary, files touched.
**Best for:** Every wiki-aware project. **Required by the bespoke-agentics wiki-first mandate when wiki/ exists.**

### B. Session Page
**Writes:** Full markdown page at `wiki/_sessions/{date}-{slug}.md` with frontmatter, conversation summary, files changed, decisions made, open questions.
**Best for:** Important work sessions you want to revisit. Pairs with the Working Memory pattern (#10) above.

### C. Diff Snapshot
**Writes:** `git diff` since session start to `.claude/sessions/{date}-{id}.patch`.
**Best for:** Reviewing what changed without committing.
**Cost:** Negligible.

### D. Confluence Sync
**Writes:** Updates or creates a Confluence page with the session summary.
**Best for:** Teams where Confluence is the source of truth and you want session work to surface there.

### E. Slack Drop
**Writes:** A short post to a channel: "Finished session on {project}. Key changes: ..."
**Best for:** Team awareness, low-friction status updates.

### F. Ticket Update
**Writes:** Appends a comment to a Jira / Linear / GitHub issue referenced earlier in the session.
**Detection:** Scan the transcript for ticket IDs (e.g., `PROJ-123`).
**Best for:** Project-tracker-driven teams.

### G. Memory Update
**Writes:** Updates the `notes.md` or `~/.claude/memory/{project}.md` file the SessionStart pattern #10 reads next time.
**Best for:** Sessions where you learned something Claude should remember.

### H. Reverse @claude: comments
**Writes:** Adds `@claude:` comments back into the codebase pointing to spots that need follow-up.
**Best for:** Pair-programming workflow. Closes the loop with SessionStart pattern #5.

### I. Desktop Notification
**Writes:** A native OS notification ("Claude finished — 12 files changed").
**Best for:** When you Cmd-Tab away during long sessions.

### J. Test Run Trigger
**Writes:** Fires off `npm test` or `pytest --quiet` as a background job, results saved to a file the next session reads.
**Best for:** TDD workflows.
**Caution:** Don't block session end on test completion; spawn and detach.

### K. Decision Capture
**Writes:** Reads the transcript for phrases like "we decided…" and writes a draft ADR.
**Best for:** Architecture-heavy work where decisions otherwise vanish into the conversation.

### L. Session Cost Log
**Writes:** Tokens used, duration, model — appended to a CSV for tracking.
**Best for:** Heavy users wanting to monitor spend.

---

## Pairing Patterns

The strongest setups pair a start hook with a stop hook:

| Pair | Effect |
|------|--------|
| #10 Working Memory + G Memory Update | Persistent project memory across sessions |
| #5 Comment Inbox + H Reverse `@claude:` | Async pair programming in code comments |
| #1 Wiki Pulse + A Wiki Log + B Session Page | Wiki is always current with session work |
| #2 Confluence Spec + D Confluence Sync | Single source of truth stays in sync |
| #7 Open PRs + F Ticket Update | Tickets advance with session output |
| #9 Second Opinion + K Decision Capture | Multi-AI deliberation with audit trail |

The interview should actively suggest these pairings.
