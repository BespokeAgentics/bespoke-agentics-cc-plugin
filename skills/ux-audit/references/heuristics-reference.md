# Heuristics & Principles Reference

## Nielsen's 10 Usability Heuristics

### H1 — Visibility of system status

The system should always keep users informed about what's going on, through appropriate feedback
within a reasonable time.

**Diagnostic questions:**

- Does every user action produce a visible response?
- Is processing time communicated (spinner, progress bar, skeleton)?
- Is the current location/state visible at all times?
- Does the page title / breadcrumb / URL reflect the current context?

**Common violations:** Silent form submissions. Buttons that appear to do nothing. No progress
indicator on long operations. Navigation that doesn't update the URL.

**Severity escalation:** Critical if user cannot tell whether their action succeeded (e.g., payment
submitted with no confirmation). High if the wait time is unknown. Medium if feedback is delayed
but eventually appears.

---

### H2 — Match between system and real world

The system should speak the users' language — words, phrases, and concepts familiar to the user,
rather than system-oriented terms.

**Diagnostic questions:**

- Are labels written in the user's vocabulary, not the developer's?
- Do icons have labels or tooltips?
- Does the workflow sequence mirror real-world task order?
- Are dates, numbers, and formats presented in the user's local convention?

**Common violations:** Error codes exposed to users ("ERR_404", "VALIDATION_EXCEPTION").
Developer-named fields ("userId", "recordType"). Reversed field order (last name before first name
in English-language forms).

---

### H3 — User control and freedom

Users often choose system functions by mistake and need clearly marked "emergency exits."

**Diagnostic questions:**

- Is there an undo for every destructive action?
- Can the user cancel a multi-step flow at any point?
- Is there a Back button or equivalent in wizards?
- Can the user dismiss modals/dialogs without completing them?

**Common violations:** Wizard flows with no Back button. Modals requiring task completion before
dismissal. Permanent deletions with no undo or recovery window. No way to cancel a running
operation.

---

### H4 — Consistency and standards

Users shouldn't have to wonder whether different words, situations, or actions mean the same thing.

**Diagnostic questions:**

- Are the same actions always labeled identically across the product?
- Do interactive elements (buttons, links, inputs) look the same throughout?
- Does the product follow platform conventions (e.g., save = Cmd/Ctrl+S)?
- Are the same colors used for the same semantic meaning throughout?

**Common violations:** "Delete" on one screen, "Remove" on another, "Discard" on a third.
Primary buttons with different colors on different pages. Non-standard keyboard shortcuts.

---

### H5 — Error prevention

Better than good error messages is careful design that prevents problems from occurring in the
first place.

**Diagnostic questions:**

- Are form fields validated in real-time (not just on submit)?
- Are destructive actions guarded by confirmation dialogs?
- Are dangerous controls visually differentiated from safe ones?
- Are constraints communicated before the user makes a mistake (not after)?

**Common violations:** Password rules revealed only after a failed attempt. Adjacent "Delete All"
and "Save All" buttons. Forms that accept invalid input and only error on server response.
Date fields that accept any string.

---

### H6 — Recognition rather than recall

Minimize the user's memory load. Make choices, objects, and actions visible or easily retrievable.

**Diagnostic questions:**

- Can the user see their options without memorizing them?
- Are previously entered values preserved and offered for re-use?
- Is context from previous steps carried forward in multi-step flows?
- Are recently used items surfaced?

**Common violations:** Command-line interfaces with no autocomplete. Multi-step forms that clear
previous answers on validation error. Dropdowns showing only codes, not human-readable names.
Search results with no history.

---

### H7 — Flexibility and efficiency of use

Accelerators allow expert users to speed up interactions. Design should serve both novices and
power users.

**Diagnostic questions:**

- Are keyboard shortcuts available for frequent actions?
- Can users customize or save common settings?
- Is there a command palette or search-based navigation?
- Are repetitive data entry patterns (same address, same config) auto-fillable?

**Common violations:** No keyboard shortcuts in tools used by power users all day. No bulk
actions for repetitive tasks. No way to save filter or view configurations.

---

### H8 — Aesthetic and minimalist design

Interfaces should not contain irrelevant or rarely needed information. Every extra unit of
information competes with relevant information.

**Diagnostic questions:**

- Is every element on the screen earning its place?
- Are rarely-used options hidden behind "advanced" toggles?
- Is the visual hierarchy clear — does the eye go to the right place first?
- Is there a clear primary action on each screen?

**Common violations:** Legacy forms with 60+ fields shown simultaneously. Status panels filled
with system metrics that 95% of users never use. Multiple competing CTAs at equal visual weight.
Decorative elements that add noise without meaning.

---

### H9 — Help users recognize, diagnose, and recover from errors

Error messages should be expressed in plain language (no codes), precisely indicate the problem,
and constructively suggest a solution.

**Diagnostic questions:**

- Do error messages say what went wrong in plain language?
- Do they tell the user what to do next?
- Are errors shown near the source of the problem (inline vs. top of page)?
- Are errors dismissible without losing the user's input?

**Common violations:** "An unexpected error occurred." "Error 500." Errors shown at top of a long
form with no indication of which field failed. Errors that clear the form on dismiss.

---

### H10 — Help and documentation

Even if the system can be used without documentation, help should be available — searchable,
focused on the task, and presented at the right moment.

**Diagnostic questions:**

- Is contextual help available at the moment of confusion?
- Is help searchable?
- Does help speak to the user's task, not the system's features?
- Are empty states used to teach rather than just show "No data"?

**Common violations:** A generic "Help" link that opens a 500-page PDF. Empty states that show
nothing instead of explaining what to do. No tooltips on complex configuration fields.

---

## Don Norman's 6 Design Principles

### N1 — Affordances

The perceived property of an object that signals how it can be used.

**Apply when:** User doesn't attempt the correct interaction (clicks non-clickable, ignores
clickable, pushes when should pull).

**Fix pattern:** Make interactive elements look interactive. Match visual treatment to function.
Clickable items need affordance signals: raised appearance, cursor change, color contrast.

---

### N2 — Signifiers

Perceptible signals that communicate where and how to act.

**Apply when:** User acts in the wrong place, or doesn't know _where_ to start. Different from
affordances — signifiers explicitly communicate.

**Fix pattern:** Add explicit labels, hints, arrows, placeholder text, helper text. An affordance
is the potential; a signifier points to it.

---

### N3 — Feedback

Every action produces a perceptible response.

**Apply when:** User repeats an action (double-clicks, resubmits a form) because they don't know
if it worked.

**Fix pattern:** Visual response within 100ms. For operations >1s: immediate acknowledgment ("Got
it, processing...") plus progress indication. For completion: clear success/failure state.

---

### N4 — Conceptual models

The user's mental model of how the system works must match the system's actual behavior.

**Apply when:** User is surprised by outcomes, takes indirect routes to accomplish tasks, or
avoids features they don't trust.

**Fix pattern:** Use familiar metaphors. Make system state visible. Ensure visual structure
mirrors logical structure. Progressive disclosure: reveal complexity only as needed.

---

### N5 — Mapping

The spatial or logical relationship between controls and their effects should be natural.

**Apply when:** User operates the wrong control, or has to memorize which control affects which
thing.

**Fix pattern:** Position controls adjacent to what they affect. Use spatial arrangement to
communicate relationship. Group related controls. Label groups, not just individual controls.

---

### N6 — Constraints

Design that limits possible actions to guide correct behavior and prevent errors.

**Apply when:** User makes errors that could have been structurally prevented.

**Fix pattern:** Physical constraints (correct input types), semantic constraints (disable
invalid options), cultural constraints (use established color conventions for danger/safety).
Show allowed options rather than rejecting wrong ones after the fact.

---

## Heuristic × Norman Cross-Reference

| Heuristic           | Primary Norman Principle | Secondary           |
| ------------------- | ------------------------ | ------------------- |
| H1 Visibility       | N3 Feedback              | N4 Conceptual model |
| H2 Real-world match | N4 Conceptual model      | N2 Signifiers       |
| H3 User control     | N6 Constraints           | N3 Feedback         |
| H4 Consistency      | N4 Conceptual model      | N5 Mapping          |
| H5 Error prevention | N6 Constraints           | N5 Mapping          |
| H6 Recognition      | N2 Signifiers            | N4 Conceptual model |
| H7 Flexibility      | N1 Affordances           | N2 Signifiers       |
| H8 Minimalism       | N4 Conceptual model      | N5 Mapping          |
| H9 Error recovery   | N3 Feedback              | N2 Signifiers       |
| H10 Help            | N2 Signifiers            | N4 Conceptual model |
