---
name: defect-intake
description: >
  User-invoked disposition of a defect found mid-session — a bug, a missing test, a swallowed
  error, a bad practice, a gap you or someone else just noticed in code nobody was asked to touch.
  Invoke only when the user explicitly asks for it ("run defect intake", "/defect-intake", "take
  this one through intake", "handle this properly before we move on"); this skill does not
  self-trigger on the mere mention of a bug, because deciding a defect is worth stopping for is the
  user's call, not an inference. It verifies the defect is real before anything is edited (an
  unreproduced defect is a hypothesis), classifies it as fix-now / fold-into-current-change /
  escalate-to-user using blast radius rather than authorship, records a baseline from the repo's
  own gates, writes the failing test first so the fix is provable, applies the narrowest fix that
  makes the test pass, re-runs the gates, documents the fix and its reasoning where that repo keeps
  durable knowledge, and returns to the interrupted work with an explicit account of what changed.
  Provenance is irrelevant to disposition: "we didn't introduce it" is not a reason to defer it.
  A failing test is never deleted, skipped, or loosened to reach green. Never commits.
---

# Defect Intake

Something is wrong in the code and you are about to decide what to do about it. That decision is
where quality is actually won or lost — not in the fix itself, which is usually easy, but in the
moment where "we didn't write this" or "that's out of scope" or "I'll note it in the summary"
becomes a reason to walk past it.

The premise of this skill is that noting a defect is not resolving a defect. A finding that
survives into a session summary, a TODO comment, or a "future work" bullet has been *deferred*,
and deferral is how defects compound: the next session inherits a codebase whose known problems are
invisible, builds on top of them, and the cost of the fix goes up every time. So the default
disposition is **fix it now, prove it, document it, then resume** — and anything other than that
default is a decision the user makes explicitly, not one you make quietly.

Three ideas govern everything below:

- **Provenance does not change the obligation.** Who introduced a defect is a fact about history,
  not about whether the software should ship broken. Do not spend a single sentence establishing
  that it was pre-existing, and never offer that as a disposition.
- **A defect is a claim, and claims get verified before they get fixed.** Fixing something you
  have not reproduced or traced produces churn at best and a new defect at worst. Verification is
  cheap; a speculative fix to working code is expensive and hard to detect.
- **Scope discipline is what makes "never defer" survivable.** A rule that says fix everything,
  applied to a codebase with unbounded latent problems, turns every task into a refactor. The
  boundary is blast radius: what blocks the current work or lives in the code you are touching
  gets fixed now; what is genuinely separate gets surfaced to the user as a decision *before* you
  proceed, not buried in a summary after.

---

## Step 0 — Take the defect in

Write down, before touching anything, what is actually being claimed:

- **The symptom.** What is observably wrong? "Login fails for SSO users" — not "the auth module is
  messy."
- **The location.** File and line, or the narrowest region you can name.
- **The evidence.** What made you believe this? A failing test, an error in output, a read of the
  code, a user report, a hunch while reading something else.
- **The class.** Bug / missing test / silent failure / contract violation / bad practice / gap.
  This drives how you verify (see Step 1) and what "fixed" means.

If several defects surfaced at once, list them all now and then work **one at a time**, all the way
through the steps, before starting the next. Interleaving fixes destroys your ability to attribute
a gate failure to a cause, and it is how a small fix quietly becomes an unreviewable diff.

If the user handed you a defect in vague terms ("something's off with the date handling"), resolve
it to a concrete symptom + location before continuing. Ask if you cannot.

---

## Step 1 — Verify it is real, before editing anything

The goal here is to convert a claim into a fact. What that takes depends on the class:

| Class | What verification means |
|---|---|
| Bug | **Reproduce it.** A failing test, a script, a command with observable wrong output. If you cannot reproduce it, say so — do not fix by inspection. |
| Missing test | Confirm the path is genuinely uncovered: search the test suite for the behavior, don't just check the file has no sibling test. Then confirm the behavior is worth pinning. |
| Silent failure | Trace the swallow to a real path where an error is discarded and something downstream depends on it having not been. |
| Contract violation | Show both sides: what the caller/type/schema/doc promises, and what the code does. |
| Bad practice | Name the concrete failure mode it enables. "This is not idiomatic" is a preference; "this mutates a shared array so concurrent callers see each other's writes" is a defect. |
| Gap | Identify what depends on the missing thing. A gap nothing depends on is a design note, not a defect. |

Two failure modes to actively guard against:

- **The phantom defect.** Reading code and thinking "that looks wrong" is a strong hypothesis and a
  weak fact. Modern codebases are full of things that look wrong and are load-bearing — the
  defensive check that seems redundant, the odd ordering that a race depends on. Before you change
  it, find out why it is that way (`git log -S`, `git blame`, the test that covers it, the comment
  above it). If you cannot find a reason and cannot demonstrate harm, downgrade it to a question
  for the user rather than fixing it.
- **The wrong root cause.** The first plausible explanation is not always the actual one. Once you
  can reproduce, confirm your explanation *predicts* the reproduction — change the input your
  theory says matters and check the symptom moves with it.

If verification kills the defect (it is not real, or it is intentional), say so plainly, record
that briefly in Step 6's documentation if it was non-obvious enough that the next reader would
also stumble on it, and resume the interrupted work. A verified non-defect is a successful intake.

---

## Step 2 — Classify the disposition

Only now, with a verified defect, decide what happens to it. Classify by **blast radius**, and note
that authorship appears nowhere in this table:

**Fix now, before anything else.** The defect blocks the current task, makes your in-flight work
incorrect, or means anything you build on top will inherit it. Also here: anything that is actively
losing data, leaking credentials, or shipping wrong results to a user. There is no version of
"finish the feature first" that is correct for these.

**Fold into the current change.** The defect is inside the blast radius of what you are already
touching — same file, same module, same call path, or something your change will make harder to
fix later. Fix it as part of this work. It is cheaper now than it will ever be again, and the
reviewer is already reading these lines.

**Escalate to the user — now, not in the summary.** The defect is genuinely separate from the
current work *and* one of these is true: fixing it would require a decision only the user can make
(a product behavior question, an API contract change, a dependency upgrade), the fix is large
enough that absorbing it silently would hijack the task the user actually asked for, or fixing it
is unsafe without information you don't have (production data shape, a migration's blast radius).

Escalation has a strict form, and it is the part most easily done badly. It means **stopping and
telling the user in the conversation, before you continue building**, with: the verified symptom,
the concrete risk of leaving it, your recommended fix, and a rough size. Then let them choose. What
escalation is *not*: a TODO comment, a bullet in a completion summary, a "noted for follow-up," a
ticket you file and move past, or a line in a handoff document. Those are all deferral wearing
escalation's clothes — the user never got a real choice, because you had already moved on by the
time they read it.

When you are genuinely torn between fold-in and escalate, prefer fixing. The asymmetry favors it:
an unnecessary small fix costs a few minutes of review, while a deferred defect costs a future
session's context, a second rediscovery, and whatever was built on top in between.

---

## Step 3 — Establish a baseline

Before editing, find out what "working" currently means, so you can tell your fix from someone
else's breakage.

Discover the repo's own gates rather than assuming a stack — read `package.json` scripts,
`Makefile`, `pyproject.toml`, CI config, or the project's `CLAUDE.md` / `CONTRIBUTING.md`, which
often names the high-signal checks directly. Run the ones relevant to the affected area (typecheck,
lint, the focused test suite; the full build only if the change could plausibly affect it).

Record what passes and what already fails. Pre-existing failures matter enormously here: if the
suite is already red, you need to know that *now*, because otherwise you will attribute it to your
fix and either chase a ghost or, worse, "fix" it by weakening a test.

If you cannot run gates at all (no install, no network, sandboxed), your evidence standard drops —
so your autonomy drops with it. Say so explicitly, make the smallest possible change, and tell the
user the fix is unverified.

---

## Step 4 — Write the failing test first

This is the step most likely to feel skippable and most likely to be the reason the fix is real.

Write a test that fails **for the reason the defect exists**, and run it to watch it fail. That
failure is the proof that the test is actually exercising the broken path — a test written after
the fix passes immediately and tells you nothing, because it may be passing for reasons unrelated
to your change. Watching it go red, then green, is the whole value.

A few things worth getting right:

- **Assert on the behavior, not the implementation.** The test should still be meaningful after a
  future refactor of the same code. If the test knows about internal call ordering or private
  helpers, it will be deleted the next time someone touches this, and the defect comes back.
- **Match the repo's test idiom.** Read a neighbouring test file first. A test that fights the
  project's conventions gets rewritten or ignored.
- **If the class is "missing test", this step is the entire fix.** Write the test, confirm it
  passes against correct behavior, and confirm it fails when you deliberately break the behavior it
  covers — otherwise you have added a test that asserts nothing.

If a test is genuinely not writable for this defect — a build config problem, a docs/type-only
issue, a race you cannot make deterministic — say why in one sentence and record what you did
instead to verify (manual reproduction, a type error that now surfaces, a check added to CI). Do
not silently skip the step; an untested fix is a claim, and the reader deserves to know which of
your claims are backed.

---

## Step 5 — Fix, narrowly, and re-verify

Make the **smallest change that turns the failing test green**. Resist the pull toward the adjacent
cleanup, the rename you would prefer, the abstraction that would have prevented this. Those may be
worth doing — but bundled into a defect fix, they hide the fix inside noise, make the change hard
to review, and make it impossible to revert the fix alone if it turns out to be wrong. If the
surrounding code genuinely needs restructuring, that is its own item: run it through Step 2 as a
separate defect.

Then re-run the gates from Step 3 and compare against the baseline:

- New failure that your fix caused → your fix is wrong or incomplete. Fix it or revert it. Do not
  leave it half-applied.
- New failure in something you did not touch → verify before assuming it is unrelated (it often is
  not — that is what a regression is).
- A test that now fails because it encoded the buggy behavior → this is the one real case for
  changing an existing test. Change it, and say explicitly in your report that you did and why the
  old assertion was wrong. This deserves the user's attention, because "the test was wrong" is also
  what it looks like when the fix is wrong.

The hard line: **a failing test is never deleted, skipped, `.only`-ed around, marked xfail, or
loosened to reach green.** Green achieved by silencing the alarm is worse than red, because red is
honest. If a test blocks you and you believe it is genuinely invalid, that is an escalation to the
user, not a decision to make alone.

---

## Step 6 — Document it where the knowledge survives

A fix nobody can find later is a fix that gets re-litigated, re-broken, or re-discovered as a
"new" defect in three months. The documentation is not bookkeeping; it is the part that stops the
same session from happening again.

Write down what the next person actually needs: **the symptom, the root cause, the fix, and — most
valuable and most often omitted — why it was wrong in the first place.** The last one is what
prevents recurrence, because the reasoning generalizes and the diff does not.

Where this goes is repo-specific, and getting it wrong (dumping it somewhere nobody reads) wastes
the step. Read `references/documentation-targets.md` for how to find the right destination in a
given repo, including repos with a wiki, an ADR directory, a changelog, or no convention at all.

Keep it proportional. A one-line null-check fix does not need a design document; a subtle
concurrency bug that took an hour to understand deserves several paragraphs, because the next
person will otherwise spend the same hour.

---

## Step 7 — Resume, with an honest account

Return to whatever the defect interrupted, and tell the user what happened in a form they can act
on. Keep it short — this is a status report, not a narrative:

- What the defect was, in one line (symptom, not saga).
- What you changed, with `file:line` references.
- The test that now covers it.
- Gate results: baseline vs. after.
- Where you documented it.
- Anything you escalated rather than fixed, and that you are waiting on them.

Do not commit. The user decides when work becomes a commit, and bundling a defect fix into a commit
they did not ask for takes that decision away from them.

Report the outcome faithfully, including the parts that went badly: if the fix is unverified, say
so; if a gate still fails, say so with the output; if you could not reproduce the defect and fixed
by inspection, say that clearly enough that the user knows to be skeptical. An intake that
overstates its own rigor is worse than one that admits its limits, because the user will trust it
the next time and be wrong to.

---

## When several defects arrive at once

Take them one at a time through the full sequence. Before starting, do one pass over the whole list
and classify each (Step 2), because the classification changes the order: anything actively causing
harm goes first, then whatever blocks the current work, then fold-ins, then escalations batched
into a single interruption rather than several.

If the list is long enough that fixing all the fold-ins would itself derail the session, that is
worth saying out loud — present the list with your classifications and let the user decide how much
to absorb now. That is a real scope decision and it belongs to them. What it is not is permission
to silently drop the tail of the list.
