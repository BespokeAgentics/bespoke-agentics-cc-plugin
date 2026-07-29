# Dissonance Catalog

Every finding the walk produces must carry exactly one rule ID from this catalog. The families
map to where in the intent→experience loop the gap opens:

- **GE\*** — Gulf of Execution: the user knows what they want but cannot see how the app does it.
- **GV\*** — Gulf of Evaluation: the user acted but cannot tell what happened.
- **MB\*** — Momentum Breaks: the flow itself fights the user's forward motion.
- **PV\*** — Promise vs. Delivery: what the product said it would do vs. what it did.

Severity is rated by **dissonance cost**, not by visual polish:

| Severity | Meaning | Test |
|----------|---------|------|
| **P0 — intent-breaking** | The user cannot achieve the stated intent, or is misled about whether they did. | Would the persona abandon or end up with a false belief about the outcome? |
| **P1 — trust-eroding** | The user succeeds but doubts, re-checks, or misunderstands what happened. | Would the persona repeat an action, go verify elsewhere, or hesitate before the next step? |
| **P2 — attention tax** | The user succeeds and knows it, but paid avoidable cognitive load. | Did the persona have to stop and think where the flow should have carried them? |

A finding's severity is the cost to the *persona from the interview*, not to a power user.

---

## GE — Gulf of Execution

### GE1 · Entry-point mismatch
The natural place where the intent forms does not offer the way to act on it.
**Walk signature:** you (as the persona) look for the action where a user would first want it, and
it isn't there — you find it later somewhere less obvious, or only via a route the UI never exposed.
**Example:** intent is "invite a teammate"; the Team page has no invite affordance — it lives under
Settings → Billing → Seats.
**Severity guidance:** P0 if the walk only progressed via a non-user trick (URL jump, DOM knowledge);
P1 if found after visible searching; P2 if found on the second look.
**Fix direction:** surface the affordance where the intent forms; duplicate entry points are cheaper
than lost users.

### GE2 · Label-vs-behavior mismatch
A control's label promises one action; activating it does another.
**Walk signature:** your pre-registered EXPECT for a click names outcome X; the OBSERVE records
outcome Y. The strongest and most mechanical rule in the catalog — the ledger proves it.
**Example:** "Save & Continue" saves but returns to the list instead of continuing; "Delete" archives.
**Severity guidance:** P0 when the actual behavior is destructive/irreversible or silently different
in meaning; P1 when the user lands somewhere recoverable but unexpected.
**Fix direction:** rename the control to what it does, or make it do what it says — never split the
difference with a tooltip.

### GE3 · Hidden prerequisite
The flow silently requires prior state that was never surfaced — the user discovers it mid-flow as
a failure.
**Walk signature:** a step fails or a control is inert because of something set up elsewhere
(verified email, permission, saved payment method, feature flag), and nothing before that step
mentioned it.
**Example:** checkout's "Place order" is disabled because no shipping address exists; the flow never
routed through adding one.
**Severity guidance:** P0 if the flow dead-ends with no path to satisfy the prerequisite from where
you stand; P1 if a path exists but costs a context switch.
**Fix direction:** either front-load the prerequisite check at flow entry or inline satisfying it at
the point of failure.

### GE4 · Vocabulary dissonance
The app's words do not match the persona's mental model — internal names, domain jargon, or
overloaded terms leak into the flow.
**Walk signature:** you hesitate over which of two options maps to the intent, or the ledger shows
an EXPECT built on the plain-English reading of a term the app uses differently.
**Example:** "Workspaces" vs "Projects" vs "Spaces" all present; the persona wants "my stuff" and
cannot tell which is theirs.
**Severity guidance:** P1 when the wrong reading leads to a wrong action; P2 when it only costs a
pause.
**Fix direction:** rename to the user's vocabulary; where a domain term must stay, define it at
first use, in place.

---

## GV — Gulf of Evaluation

### GV1 · Silent success
An action completes but nothing tells the user it did.
**Walk signature:** ACT succeeds (verified by later state or a reload), but OBSERVE at the moment of
action records no confirmation — no toast, no state change in view, no navigation.
**Example:** "Add to list" fires a request and changes nothing visible; the persona clicks again,
creating a duplicate.
**Severity guidance:** P0 when repeating the action causes harm (double charge, duplicate record);
P1 otherwise — the user *will* re-check.
**Fix direction:** confirm at the point of action, in the user's line of sight, with what changed.

### GV2 · Ambiguous state
After an action, the screen does not disclose whether the system state matches what the user asked
for.
**Walk signature:** your OBSERVE cannot honestly answer "did it work?" from what is on screen — you
had to infer, reload, or navigate away to find out.
**Example:** toggling a setting shows the toggle moved, but a banner still describes the old
behavior.
**Severity guidance:** P1 by default; P0 when the ambiguity covers something consequential
(payment, publication, deletion).
**Fix direction:** make the post-action screen state the answer to "what is true now".

### GV3 · Progress opacity
A multi-step flow gives no sense of place: how far along, what remains, whether steps can be
revisited.
**Walk signature:** at any mid-flow step you cannot state (from the screen alone) how many steps
remain or whether Back is safe.
**Example:** an onboarding wizard with no step indicator; the persona doesn't know if the next
"Continue" commits everything.
**Severity guidance:** P2 by default; P1 when a step is irreversible and nothing marks it as the
point of no return.
**Fix direction:** show position and remaining cost; mark commitment points before they are crossed.

### GV4 · Feedback contradicts state
The UI asserts something that is not true — "Saved" when it wasn't, a success toast over a failed
request, a count that doesn't include the item just added.
**Walk signature:** OBSERVE records a positive assertion; a later step (or reload) reveals the
system state disagrees. The most trust-destroying rule in the catalog.
**Example:** profile edit shows "Changes saved", but revisiting shows the old values.
**Severity guidance:** P0 always. A false positive teaches the user that the product's word is
worthless.
**Fix direction:** tie feedback to confirmed state (server ack, re-read), never to the click.

---

## MB — Momentum Breaks

### MB1 · Context eviction
Mid-task, the flow dumps the user somewhere unrelated and expects them to find their way back.
**Walk signature:** a step's OBSERVE lands on a screen with no visible relation to the flow —
dashboard, homepage, a different entity — while the task is incomplete.
**Example:** creating an item redirects to the global list at page 1 instead of the item just
created; verifying email opens a marketing page.
**Severity guidance:** P1 by default; P0 if the way back requires reconstructing lost context
(which record was I on?).
**Fix direction:** end every step where the *next* step begins.

### MB2 · Data loss on transition
Entered data evaporates on back, error, validation failure, or navigation.
**Walk signature:** you fill a form, something interrupts (error, Back, a required detour), and the
fields return empty.
**Example:** a validation error on one field clears the whole form; opening the ToS link and
returning wipes the signup.
**Severity guidance:** P0 when the lost input is long or hard to reconstruct; P1 for short forms.
**Fix direction:** persist input across every transition the flow itself can cause.

### MB3 · Dead end
A state with no forward affordance: an error, empty state, or terminal screen from which the flow
offers no recovery or next step.
**Walk signature:** OBSERVE records a screen where no visible control advances the intent — the
only options are browser Back or giving up.
**Example:** "Something went wrong" with no retry; an empty search results page with no way to
broaden or ask differently; a 404 after a flow-internal link.
**Severity guidance:** P0 when it occurs on the flow's happy path; P1 on a branch.
**Fix direction:** every terminal state names the next move — retry, alternative, or a way back
with context intact.

### MB4 · Re-asking known information
The flow demands information the product already holds.
**Walk signature:** a form field asks for something you (as this account/session) already provided,
observable elsewhere in the product.
**Example:** checkout asks for the email the user is logged in with; a support form asks which plan
you're on.
**Severity guidance:** P2 by default; P1 when the re-asked data is long or error-prone (addresses,
IDs) so re-entry risks divergence.
**Fix direction:** prefill and let the user correct, rather than ask and make them retype.

### MB5 · Interruption hijack
Something seizes the screen mid-task on the product's agenda, not the user's.
**Walk signature:** between your ACT and the intended next step, a modal/overlay/tour appears that
is unrelated to the intent, and dismissing it costs attention or (worse) derails state.
**Example:** an NPS survey mid-checkout; a feature-announcement modal on first entering the flow's
key screen.
**Severity guidance:** P2 when dismissal is one obvious action; P1 when dismissal is ambiguous or
the interruption recurs within the same walk.
**Fix direction:** defer product-agenda interruptions to task boundaries — never between a user and
an in-flight intent.

---

## PV — Promise vs. Delivery

### PV1 · Framing-vs-flow gap
The screen that sold the action framed an outcome the flow does not deliver.
**Walk signature:** the entry screen's copy (landing section, empty state, menu item description)
set the EXPECT for the whole flow, and the flow's end state doesn't match it.
**Example:** "Get your report in seconds" leads to a flow ending in "We'll email you within 24
hours"; "Free trial" ends at a credit-card wall.
**Severity guidance:** P0 when the delivered outcome differs in kind (trial → payment, instant →
queued); P1 when it differs in degree.
**Fix direction:** fix whichever is wrong — the promise or the flow — and check they're owned by
the same team.

### PV2 · CTA promise broken
A specific call-to-action implies an immediate outcome and delivers an intermediary instead.
**Walk signature:** EXPECT (from the CTA's own words) names a result; OBSERVE records a form,
paywall, waitlist, or contact-sales page. The scoped, single-control version of PV1.
**Example:** "Download" opens a lead-capture form; "Start now" opens a scheduling page for a demo.
**Severity guidance:** P1 by default; P0 when the intermediary collects something valuable (payment
details, personal data) under the broken promise.
**Fix direction:** make the CTA name the very next thing that happens.

### PV3 · Defaults contradict stated intent
The flow's pre-selected choices work against what the user just expressed.
**Walk signature:** after a step where the persona stated a preference (picked a plan, chose an
option, answered a question), a later step defaults to the opposite or to the product-favorable
choice, and accepting defaults would betray the intent.
**Example:** user picks "Personal" use; the next screen defaults to the Team plan with annual
billing pre-selected.
**Severity guidance:** P0 when accepting the defaults commits money or data sharing; P1 otherwise.
**Fix direction:** propagate every expressed choice forward; defaults should encode the user's
stated intent, not the growth team's.

### PV4 · Completion mismatch
The flow's "done" state is not the intent's "done" state — technically complete, goal not achieved.
**Walk signature:** the end-of-walk thread test fails: the final OBSERVE doesn't satisfy the
success criterion frozen in Phase 1, even though the flow congratulated itself.
**Example:** intent was "create an account and reach a usable starting screen"; the flow ends on
"Check your email" with the product unusable until a verification that wasn't framed as part of
signup.
**Severity guidance:** P1 by default; P0 when the user is left believing they're done and they are
not (the appointment isn't booked, the listing isn't live).
**Fix direction:** either extend the flow to real completion or reframe honestly what this flow
completes.

---

## Classification discipline

- **One finding per root cause.** If three steps all stumble on the same vocabulary term, that is
  one GE4 finding with three evidence entries — not three findings.
- **The ledger is the evidence.** A GE2/PV2 finding is only claimable when the pre-registered
  EXPECT is in the ledger *before* the ACT. An expectation reconstructed afterward is hindsight;
  downgrade it to an observation, not a finding.
- **Dissonance ≠ bug.** A crash is a defect, not necessarily dissonance — classify it MB3 only for
  its dead-end quality, and note the defect separately for the report's observations section.
- **When two rules fit, pick where the gap *opened*,** not where it was felt: a broken promise
  discovered at step 6 that was made at step 1 is PV1 (opened at framing), not GV2.
