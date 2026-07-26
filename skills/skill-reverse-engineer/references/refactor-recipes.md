# Refactor recipes — the extraction quality bar

Read this before Phase 5. Every artifact this skill creates must clear these bars; an extraction
that fails them makes the target *less* robust than the prose it replaced.

## The prime directive: behavior-preserving

Every refactor keeps the target skill doing the same job — the same deliverables, the same
phases, the same user experience — with less of it improvised per run. If an extraction would
change behavior (the script can't cover a case the prose handled, a template forecloses a
variation the skill needs), stop and surface the tension instead of shipping the change.

## Recipe 1 — Extracting a script (DS1–DS4)

**The script itself:**
- Shebang, and `chmod +x`.
- Usage message + nonzero exit on missing/invalid arguments. Argument parsing appropriate to the
  language (`argparse`, `getopts`, explicit `"$1"` checks) — never positional assumptions with no
  validation.
- Nonzero exit on any failure; no silent-failure constructs (`|| true`, bare `except: pass`)
  unless the specific failure is genuinely ignorable, with a comment saying why.
- Output contract: print results in a stated, parseable form (paths, JSON, counts). The SKILL.md
  instruction that invokes the script says what to do with the output.
- No hardcoded absolute paths. Inputs and output locations are arguments. Stdlib/coreutils only
  unless the target skill already declares a dependency.
- Prefer the target skill's existing script language; otherwise `bash` for orchestration/file
  ops, `python3` for parsing/aggregation.

**The rewritten SKILL.md step — keep the why, move the how:**

Before:
> Extract frames from the video every 2 seconds using ffmpeg (`-vf fps=0.5`), naming them
> `frame-%04d.jpg`. Then write a manifest.json listing each frame with its timestamp so later
> phases can reference moments by time.

After:
> Extract frames and the timestamp manifest (later phases reference moments by time):
> ```bash
> scripts/extract_frames.sh <video> <interval-seconds> <outdir>
> ```
> Prints the manifest path on success.

The rationale clause survives; the mechanics live in exactly one place. Never leave the prose
procedure *and* the script both describing the how — that is AM3 drift waiting to happen.

**Prove it ran.** Execute the script in this session: the usage path (bad args → usage + nonzero
exit) and a happy path against a fixture in the scratchpad. A script that has never executed does
not ship. If the runtime isn't available here, say so in the report and mark the script
"not executed" — never imply it was tested.

## Recipe 2 — Freezing a template (TP1–TP3)

- Literal file in `templates/` (multi-file or reused artifacts) or a fenced block in a reference
  (single short structure). Placeholders as `{{SCREAMING_SNAKE}}`, each listed at the top of the
  template (or beside it) with one line on what fills it and from where.
- Everything non-placeholder is verbatim — the point is that the skeleton stops varying. If a
  section is genuinely optional, mark it (`{{#IF_X}}…{{/IF_X}}` or an HTML comment convention)
  rather than describing optionality in distant prose.
- The instruction becomes "copy/fill this template", and names the source of each slot's content.
- For TP3: the example is a *complete, real* instance — produced by actually filling the
  template once — not a sketch.

## Recipe 3 — Tightening a contract (CT1–CT3)

- **Intermediate state (CT1):** a named file at a stated path, JSON unless there's a reason.
  Give the schema as a commented example instance (models read examples better than JSON Schema),
  plus one line per field. The consuming phase reads the file, not its memory of the producing
  phase.
- **Subagent packets (CT2):** the prompt lives in the skill's files as a verbatim template with
  `{{SLOTS}}`; the return contract is explicit ("Return ONLY JSON: {…}"). When the harness
  supports schema-enforced returns, say to use it.
- **Argument grammar (CT3):** one canonical block near the top of SKILL.md (or the command file —
  one of them, pointed to by the other): every flag, its default, and precedence when flags
  interact. Delete duplicate partial grammars elsewhere.

## Recipe 4 — Wiring a check (VF1–VF3)

- Each accepted eyeball check becomes: the exact command + the expected result, placed where the
  claim is made — or a line in a single `scripts/verify.sh` that runs all of them and fails
  loudly on the first miss (prefer the aggregate script once there are 3+ checks).
- Checks must be decidable: exit codes, counts, existence, schema-validity, grep-zero. Anything
  requiring judgment stays judgment — give it a rubric and (if warranted) a fresh-context grader
  per VF3, but do not fake determinism with a check that can't actually decide.
- Wire the checks into the target's verify phase so they run by default, not on request.

## Recipe 5 — Resolving ambiguity (AM1–AM4)

- AM1: replace the vague quantifier with the real condition. If the condition is unknowable at
  write time, it is a user gate — say so and route it to the skill's interview.
- AM2: per dependency: how it's detected, the stated fallback, and how the degraded output is
  labeled. House these in one degradation section; inline only when a single step is affected.
- AM3: pick the winning location (usually the deeper reference for detail, SKILL.md for the
  pointer), rewrite the loser as a pointer.
- AM4: number the phases; state each gate's invariant once, at the gate.

## Recipe 6 — Cutting bloat (RB1–RB3)

- RB1: for each load-bearing MUST, add the enforcement (gate/check/script refusal), keep one calm
  sentence of why, delete the volume. A MUST with enforcement attached is allowed to stay MUST.
- RB2: delete. Do not compress into terser filler — remove.
- RB3: restructure so SKILL.md carries the spine (always-needed flow + explicit "read X before
  phase Y" pointers) and references carry depth. Moving text counts as a refactor: verify the
  pointers after moving.

## Recipe 7 — Materializing knowledge (KM1–KM5)

Formats and policy live in `references/materialization.md` (the materialization test, the
anti-list, `_provenance`, placement, honesty labels) — this recipe is the build discipline.

**The generator** — everything in Recipe 1's script bar, plus:
- **Deterministic output**: sorted keys, stable ordering — regenerating against unchanged
  sources produces a byte-identical artifact, so diffs are meaningful.
- Idempotent; never writes outside its `--out` target.
- Embeds the `_provenance` block (first key) with source paths + sha256 hashes and its own
  `regenerate` / `check` command lines.
- Implements `--check <artifact>`: recompute source hashes, exit 0 fresh / 3 stale (distinct
  from the generic failure exit so callers can branch).

**The artifact** — valid JSON; `_provenance` first; `facts` shaped for the *consuming decision*
(keyed by the question the skill asks, not by the source's layout — a validator wants
`facts.question.status = [...]`, not a transcription of the schema document's structure).

**The consuming rewrite** — keep the why, move the what. Worked example (the wiki-lint enum
case, a KM5):

Before:
> Validate frontmatter: `question` pages require `status` ∈ {open, resolved, blocked}.

After:
> Validate frontmatter against `wiki/_schema/generated/frontmatter-matrix.json` (run its
> `--check` first; stale → regenerate; generator unavailable → validate against
> `wiki/_schema/SCHEMA.md` directly and label the report "derived fresh — artifact stale").
> The matrix exists so the vault's schema, not this file, defines validity.

**The anti-recipe** — before writing any generator, re-apply the materialization test and
anti-list in `references/materialization.md`. One compact machine-readable source answering the
question → point at it; no defining source → it's judgment or a `declared` interview fact. An
artifact that fails these tests is a KM5 defect the moment you ship it.

**Parity** — the artifact's facts must match what a careful fresh derivation from the sources
finds; Phase 6 spot-checks at least one mined fact per artifact against its cited source line.

## The parity checklist (run after all refactors, before Phase 6 verification)

- [ ] Every deliverable the original produced, the refactored skill still produces, same
      locations, same (or template-pinned) shapes.
- [ ] Every phase of the original flow survives, same order, same gates.
- [ ] Every degradation path the original handled is still handled (and new AM2 paths added).
- [ ] No instruction references a file that doesn't exist; no shipped file is referenced by
      nothing.
- [ ] The why-prose for each extracted step survived next to its invocation.
- [ ] Every materialized artifact's facts spot-checked against its cited sources; every
      consuming instruction states its stale/absent fallback.
- [ ] Nothing in the diff changes what the skill *decides* — only where the mechanics execute.
