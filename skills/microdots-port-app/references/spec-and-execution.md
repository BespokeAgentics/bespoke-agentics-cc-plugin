# Phases 5–7 — Spec seeding, elicitation, execution

## Phase 5 — Seed the spec

spec-elicitation's documented way to receive context is a partial spec file at
the path it is given: its first phase reads the file, assesses completeness,
and interviews on what is missing. So the handoff _is_ the pre-write — fill
everything the dossier can answer, cite every claim, and leave what only the
user can decide as `TODO — not yet elicited`. A confidently seeded wrong
answer is the one thing the interview is bad at catching; sections the
evidence cannot support stay TODO.

Write to `<dossier>/spec.md` using the spec-elicitation template's section
headers. The mapping:

| Spec section                                | Seed from                                             | Notes                                               |
| ------------------------------------------- | ----------------------------------------------------- | --------------------------------------------------- |
| Executive Summary                           | trace summary + confirmed composition                 | What is being ported and into how many dots         |
| Target Users & Scale                        | inventory (roles walked) + trace (auth lane)          | Often partly TODO — scale is a user answer          |
| Core Functionality                          | behavior lane + interaction log, grouped per dot      | Workflows as observed, each anchored                |
| Technical Architecture → Data Model         | contract drafts + storage sections                    | Port map §3b/§3d, per dot                           |
| Technical Architecture → Integration Points | public surfaces + brokered seams + external services  | Attributes, events, what the host brokers           |
| Technical Architecture → State Management   | TEA sketches                                          | Port map §3c, per dot                               |
| Security & Compliance                       | D-auth row + auth touchpoints + secrets found         | Present the options; the interview decides          |
| Edge Cases & Error Handling                 | error states observed + statuses seen + trap register | The inventory's error states are gold here          |
| UX Considerations                           | state catalog + screenshots + D-ux                    | Reference `ui/state-*.png` by name                  |
| Future Considerations → Out of Scope        | `defer` dispositions + D-scope                        | Explicit, with reasons                              |
| Assumptions & Open Questions                | **the decision register, embedded whole**             | One row per open decision                           |
| References                                  | the dossier files                                     | trace.md, ui-inventory.md, port-map.md, screenshots |

Mark the header block Status: Draft. `--dossier-only` stops after this write.

**Monorepo mode addition:** the target repo's law says plans are authored in
its wiki. After Phase 6 settles the spec, file it as a `decision` page in
`wiki/plans/active/` following `wiki/_schema/SCHEMA.md` (read the schema
first; cite `file.ts:line` sources; include the done-bar). The dossier spec
stays the working copy; the wiki page is the record.

## Phase 6 — Elicit

Invoke the `spec-elicitation` skill with the dossier's `spec.md` path, and let
it run its own process. Do not duplicate its interview beforehand, do not
answer register rows on the user's behalf, and do not trim its dimensions: a
well-seeded spec shrinks the interview naturally.

When the interview finishes, reconcile: flip the settled decision-register
rows to `decided` in `port-map.md`, so the register and the spec never
disagree. If the skill is unavailable, leave the seeded spec and register in
place and say plainly the interview still needs to run — a seeded spec is a
draft, not an approval.

## Phase 7 — Execute

### The gate

Nothing outside the dossier directory is created or edited before this gate.
One AskUserQuestion:

- Confirm each MicroDot's name (lower-kebab) and each tag.
- How far: **full implementation** · **scaffold only** · **stop at the spec**.
- For a large port (the disposition tables run long, several dots), offer the
  orchestrate handoff as an explicit option — the spec plus the port maps is
  exactly the plan a multi-agent build consumes.

`--mode` presets the ceiling; the gate can choose less, never more.

### Scaffold

**Monorepo:** run `bun run new:microdot <name>` per dot, then the wiring steps
the repo's `AGENTS.md` lists — tsconfig paths, vitest aliases, registry entry,
`index.html` section + slot, `host-topology.json` route + slot declaration.
The repo's topology tests fail on a mounted-but-undeclared or
declared-but-missing slot; run them before calling the scaffold done. Never
reimplement the generator or the wiring rules here.

**Standalone:** build the workspace per `references/standalone-scaffold.md`,
ending with the scaffold's own check green.

### Implementation waves

Work each dot's disposition table top to bottom in four waves. Each wave ends
with the workspace check green (monorepo: `bun run check`; standalone: the
scaffold's check script) before the next begins — a wave that leaves the tree
red has not finished. With several dots, complete a wave across all dots
before advancing (contracts everywhere, then services everywhere, …) so the
brokered seams are designed against real contracts, not guesses.

1. **Contract + client.** Real RPCs, schemas (effect Schema — the zod
   translation from the optimization register happens here), tagged errors;
   the client stays a function of its base URL.
2. **Service.** The store seam if stateful (interface + adapters), handlers
   (platform-free), migrations, the wire-level service test, secrets failing
   closed with the unset case tested. A one-off data import, if D-data chose
   one, is built and tested here, flagged as such.
3. **TEA app.** Model, Messages, `update`, `view`, `subscriptions` per the
   sketch. Story tests for the update logic — **each UI state observed in
   Phase 2 gets a story test where sensible; that is what behavior
   preservation means in a re-expression.**
4. **Element + styles + host.** Attributes and events per the public surface,
   the dot's own stylesheet on theme tokens, multi-tag registration where the
   composition said so, and the host wiring (monorepo: registry/topology;
   standalone: the mini-host) — including the broker, only after the poll-only
   path demonstrably works.

Throughout: the disposition table is the worklist. A disposition that proves
wrong mid-wave is **corrected in `port-map.md` in the same breath** — and
noted for Phase 8, because a wrong disposition is exactly what the port memory
exists to stop recurring. Keep the trap register open next to the wave it
threatens.

### Verify

**Monorepo:** invoke the repo's `verify` skill and let its bar be the done
bar. **Standalone:** run the equivalent sequence in
`references/standalone-scaffold.md` § Verify. Either way: static checks green,
every bundle built, the system booted, and every dot confirmed **in a
browser** — rendering real content, polling its service, reacting to its
attributes, surviving unmount/remount. If the browser step could not be
completed, the report says so — the port is then _built_, not _verified_.

### Catalog maintenance (monorepo mode)

If this port shipped something genuinely reusable, append the catalog entry
and its Trigger-index row now, in this run, per the catalog's own template. A
whole-app port is the single most likely event to mint new patterns, because
it imports shapes the workspace has never needed before.

### Deploy — never

Point at the target's deploy path (the monorepo's deploy skill, or the
Workers/CDN direction the dot's D-deploy row records) and stop. Deploying
publishes publicly and creates account resources; it has its own
confirmations, and this skill does not borrow them.

## The report

End every run — whatever mode it stopped at — with:

- Where the run stopped and why (mode ceiling, gate choice, or a blocker).
- The composition shipped vs. proposed, and who decided.
- The dossier paths, and the spec's status (Draft / interviewed / approved;
  monorepo mode: the wiki page filed).
- Ported / adapted / dropped / deferred — counts plus the notable rows.
- Dispositions corrected mid-flight, and what that says about the port maps.
- What verify actually observed, verbatim where it matters — or that it did
  not run.
- Traps hit despite the register; catalog entries added or fixed.
- Memory rows added, reinforced, or annotated (Phase 8), and the reminder
  that the plugin repo needs a commit.
- What remains: deploy (never run from here), deferred decisions, D-old-app's
  recorded intent for the source application.

Honest accounting is the deliverable: a port that dropped three subfeatures
and says so is a success; one that dropped them silently is a defect with good
posture. Nothing is committed; the source app was never touched.
