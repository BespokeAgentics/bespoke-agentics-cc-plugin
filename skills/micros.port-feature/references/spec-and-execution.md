# Phases 5–7 — Spec seeding, elicitation, execution

## Phase 5 — Seed the spec

spec-elicitation's documented way to receive context is a partial spec file at
the path it is given: its first phase reads the file, assesses completeness,
and interviews on what is missing. So the handoff *is* the pre-write — fill
everything the dossier can answer, cite every claim, and leave what only the
user can decide as the template's `TODO — not yet elicited`. Sections the
evidence cannot support stay TODO; the interview exists to fill gaps, not to
audit fabrications, and a confidently seeded wrong answer is the one thing the
interview is bad at catching.

Write to `<dossier>/spec.md` using the spec-elicitation template's section
headers. The mapping:

| Spec section | Seed from | Notes |
|---|---|---|
| Executive Summary | trace summary + feature pointer | What is being ported and why it stands alone |
| Target Users & Scale | inventory (roles walked) + trace (auth lane) | Often partly TODO — scale is a user answer |
| Core Functionality | behavior lane + interaction log | Workflows as observed, each anchored |
| Technical Architecture → Data Model | contract draft + storage section | From port-map §2/§4 |
| Technical Architecture → Integration Points | public surface + external services | Attributes, events, external calls |
| Technical Architecture → State Management | TEA sketch | From port-map §3 |
| Security & Compliance | D-auth row + auth touchpoints | Present the options; the interview decides |
| Edge Cases & Error Handling | error states observed + statuses seen + trap register | The inventory's error states are gold here |
| UX Considerations | state catalog + screenshots | Reference `ui/state-*.png` by name |
| Future Considerations → Out of Scope | `defer` dispositions + D-scope | Explicit, with reasons |
| Assumptions & Open Questions | **the decision register, embedded whole** | The interchange artifact — one row per open decision |
| References | the dossier files | trace.md, ui-inventory.md, port-map.md, screenshots |

Mark the header block Status: Draft. `--dossier-only` stops after this write.

## Phase 6 — Elicit

Invoke the `spec-elicitation` skill with the dossier's `spec.md` path as its
argument, and let it run its own process — it reads, assesses, and interviews
until every dimension is settled and the user confirms completeness. Do not
duplicate its interview beforehand, do not answer register rows on the user's
behalf, and do not "help" by trimming its dimensions: a well-seeded spec
shrinks the interview naturally, because settled-with-evidence reads as
settled.

When the interview finishes, reconcile: flip the decision-register rows it
settled to `decided` in `port-map.md`, so the register and the spec never
disagree about what was chosen.

If the skill is unavailable, leave the seeded spec and the register in place
and say plainly that the interview still needs to run before execution — a
seeded spec is a draft, not an approval.

## Phase 7 — Execute

### The gate

Nothing outside the dossier directory is created or edited before this gate.
One AskUserQuestion:

- Confirm the micro name (lower-kebab; the generator rejects anything else).
- How far: **full implementation** · **scaffold only** · **stop at the spec**.
- For a large port (the disposition table runs long, the source feature is
  thousands of lines), offer the orchestrate handoff as an explicit option —
  the spec plus the port map is exactly the plan a multi-agent build consumes,
  and grinding a huge port inline is a worse use of the session than
  orchestrating it.

`--mode` presets the ceiling (`spec` and `scaffold` stop there); the gate can
always choose less than the ceiling, never more.

### Scaffold — invoke `new-micro`

Invoke the `new-micro` skill with arguments `<name> <brief>`. The brief is one
to three sentences distilled from the spec that *names the catalog-matched
needs in the trigger words the catalog indexes* — gating, persistence,
polling, streaming, admin dashboard — so new-micro's own prior-art protocol
matches and ports the patterns. Never reimplement the scaffold, the wiring, or
the prior-art porting here: new-micro owns them, and a fork of that logic in
this skill would drift from it within a month.

After it reports: the workspace now has a wired, bootable placeholder micro
with matched patterns ported. `--mode scaffold` stops here.

### Implementation waves

Work the disposition table top to bottom in four waves. Each wave ends with
the workspace's own check command green (typecheck, lint, tests) before the
next begins — a wave that leaves the tree red has not finished.

1. **Contract + client.** The real RPCs, schemas, and tagged errors from the
   port map replace the scaffold placeholders; the client stays a function of
   its base URL.
2. **Service.** The store seam (interface + shared SQL + one adapter per
   platform) if stateful, handlers (platform-free — the workspace's rules say
   which imports are allowed where), migrations, and the wire-level service
   test. If the spec chose a one-off data import, it is built and tested here,
   flagged as such.
3. **TEA app.** Model, Messages, `update`, `view`, `subscriptions` per the
   sketch. Story tests for the update logic — **each UI state observed in
   Phase 2 gets a story test where sensible; that is what behavior
   preservation means in a re-expression** — plus scene tests for key markup.
4. **Element + styles.** Attributes and events per the public surface, the
   CSS prologue the workspace mandates, semantic tokens only, and the
   multi-tag conversion if D-tags said several.

Throughout: the disposition table is the worklist. A disposition that proves
wrong mid-wave (the shared export does not cover the case; the copy-adapt
needs more surgery than reimplementing) is **corrected in `port-map.md` in the
same breath** — the dossier stays truthful, or it stops being consulted. Keep
the trap register open next to the wave it threatens; when a trap bites
anyway, note it in the report so the register grows teeth.

### Verify — invoke `verify`

Invoke the `verify` skill and let its bar be the done bar: static checks,
every bundle built, the system booted, and the micro confirmed **in a
browser** — rendering real content, polling its service, reacting to its
attributes, surviving unmount/remount. Green static checks alone do not make a
port done in a system whose runtime forks and swallows startup defects. If the
browser step could not be completed, the report says so — the port is then
*built*, not *verified*.

### Catalog maintenance

If this port shipped something genuinely reusable — a pattern the next micro
would otherwise rebuild — append the catalog entry and its Trigger-index row
now, in this run, per the catalog's own template. Rotted entries found in
Phase 3 were fixed then; this is the other half of the duty. A port is the
single most likely event to mint a new pattern, because it imports shapes the
workspace has never needed before.

### Deploy — never

Point at the `deploy` skill and stop. Deploying publishes publicly and creates
account resources; it has its own confirmations and its own skill, and this
one does not borrow them.

## The report

End every run — whatever mode it stopped at — with:

- Where the run stopped and why (mode ceiling, gate choice, or a blocker).
- The dossier paths, and the spec's status (Draft / interviewed / approved).
- Ported / adapted / dropped / deferred — counts plus the notable rows.
- Dispositions corrected mid-flight, and what that says about the port map.
- What verify actually observed, verbatim where it matters — or that it did
  not run.
- Traps hit despite the register; catalog entries added or fixed.
- What remains: deploy (never run from here), deferred decisions, D-old-app's
  recorded intent for the source application.

Honest accounting is the deliverable: a port that dropped three subfeatures
and says so is a success; one that dropped them silently is a defect with good
posture. Nothing is committed; the source repo was never touched.
