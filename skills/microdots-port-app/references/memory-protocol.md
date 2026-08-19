# Phases 0 & 8 — The port memory

The memory exists for one outcome: the second port of a React+zod+Express app
should spend its effort on what is _different_ about this app, not on
re-deriving that zod becomes effect Schema. It stores **this skill's own port
history** — never a copy of the target's rules, which are read at runtime and
would rot here.

## Memory home resolution (Phase 0)

1. The skill's own `memory/` directory inside the plugin's git checkout:
   `ls -d ~/.claude/plugins/marketplaces/*/skills/microdots-port-app/memory`
   — the first hit wins. This is the durable home: versioned with the skill,
   committed by the user, shared across that user's machines via the plugin
   repo.
2. Fallback: `~/.claude/bespoke-agentics/port-memory/` (create it). Warn that
   the ledger is outside the plugin repo and will not travel.

Never write memory into the plugin _cache_ (`~/.claude/plugins/cache/...`) —
a plugin update silently discards it.

## `memory/stack-mappings.md` — the mapping ledger

One table, append-and-annotate, never rewrite:

```markdown
| ID  | Source pattern (fingerprint terms) | Target idiom                  | Default disposition | Confidence | First / last port           | Notes             |
| --- | ---------------------------------- | ----------------------------- | ------------------- | ---------- | --------------------------- | ----------------- |
| M1  | zod schemas shared client/server   | effect Schema in the contract | reimplement         | 1/1        | 2026-08-19 spec-interviewer | v4 Schema, not v3 |
```

- **Fingerprint terms** — the words a trace would surface: framework, state
  management, schema library, server shape, persistence, streaming, auth,
  notable SDKs. Matching is by terms, not exact stacks.
- **Confidence** — `applied-cleanly / times-applied`. A row at 4/4 is close to
  deterministic; a row at 1/3 is a warning label, and its Notes say what went
  wrong.
- Rows are never deleted. A row that proved wrong gets its denominator
  incremented and a dated note; if a better mapping replaced it, the note
  names the successor row.

## `memory/ports/<date>-<slug>.md` — one record per port

```markdown
# Port record — <slug>

Date · source app path · target mode (monorepo/standalone) · run outcome
(verified / built / stopped at <phase>)

## Stack fingerprint

framework · state mgmt · schema lib · server · persistence · streaming · auth · notable SDKs

## Composition

Proposed candidates → what the user chose, and why (one line each).

## Decisions

The decision register's final state, one line per row: ID → choice → decided/assumed.

## Mappings exercised

| Ledger ID (or NEW) | Held / proved wrong | Note |

## Dispositions corrected mid-wave

What the port map got wrong and what the correction was — the highest-value
lines in the record.

## Traps hit

Despite the register — each with symptom → cause, so it can be matched next time.

## Verify

What the browser actually showed, one line per dot — or "did not run".
```

## Phase 0 — Read protocol

1. Read `stack-mappings.md` whole (it is one table).
2. Grep `ports/` for the source app's fingerprint terms; read matching
   records.
3. Carry matches forward: matched mapping rows enter the Phase 4 optimization
   register with provenance `prior` (naming the ledger ID); matched
   composition and decision outcomes become the _recommendations_ in the
   proposal and register — recommendations, never pre-decisions. The user
   still confirms composition every run.
4. No matches → say so in one line and continue. This port seeds the rows.

## Phase 8 — Write protocol

Run after verify, or at wherever the run actually stopped (the record's
outcome field is honest about which):

1. Append the port record.
2. Update the ledger: `novel` optimization-register rows from Phase 4 become
   new mapping rows (next ID); `prior` rows that held get their numerator and
   denominator incremented; rows that proved wrong get the denominator and a
   dated note.
3. Tell the user the plugin repo has uncommitted memory changes — **the skill
   never commits**. An uncommitted ledger is one `plugin update` away from
   silent loss, so say it plainly, every run.

## What the memory is not

- Not a cache of target law (AGENTS.md, the catalog, invariants) — always
  read those at runtime.
- Not a substitute for the interview — a `prior` provenance shrinks a
  question, never removes the user's right to answer it differently.
- Not an approval trail — decisions live in the dossier and the spec; the
  memory records them for _matching_, not as authority.
