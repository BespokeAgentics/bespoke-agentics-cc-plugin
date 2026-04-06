# Code Pattern Detection Library

For each pattern below: search for the anti-pattern, flag it with the heuristic + Norman
principle, severity, and the recommended fix. Always report file + line number.

---

## H1 — Visibility of system status

### P1.1 — Button with no loading state

**Anti-pattern:** onClick handler that calls async function with no in-flight state

```jsx
// BAD
<button onClick={handleSubmit}>Submit</button>;

async function handleSubmit() {
  const result = await submitData();
}
```

**Look for:** `async` functions attached to button `onClick` with no `loading` / `isSubmitting`
state, no disabled state during operation, no spinner.

**Fix:**

```jsx
const [isSubmitting, setIsSubmitting] = useState(false);

<button onClick={handleSubmit} disabled={isSubmitting}>
  {isSubmitting ? <Spinner /> : "Submit"}
</button>;

async function handleSubmit() {
  setIsSubmitting(true);
  try {
    await submitData();
  } finally {
    setIsSubmitting(false);
  }
}
```

**Heuristic:** H1 | **Norman:** N3-Feedback | **Severity:** High

---

### P1.2 — Async data fetch with no loading UI

**Anti-pattern:** `useEffect` fetching data with no loading state rendered

```jsx
// BAD
useEffect(() => { fetchData().then(setData); }, []);
return <div>{data?.items.map(...)}</div>; // blank until loaded
```

**Fix:** Add `isLoading` state; render skeleton or spinner while loading.
**Heuristic:** H1 | **Norman:** N3-Feedback | **Severity:** Medium

---

### P1.3 — Missing success/error feedback after mutation

**Anti-pattern:** Form submission or data mutation with no toast, banner, or state change.

```jsx
// BAD
const handleSave = async () => {
  await api.save(formData);
  // nothing happens visually
};
```

**Look for:** API calls in handlers with no subsequent state update, toast, redirect, or
visible confirmation.
**Heuristic:** H1 | **Norman:** N3-Feedback | **Severity:** High

---

### P1.4 — No URL update on navigation

**Anti-pattern:** SPA routing that changes view without updating URL/history.
**Look for:** `setState` calls that switch between major views without `router.push()` or
`history.pushState()`.
**Heuristic:** H1 | **Norman:** N4-Conceptual model | **Severity:** Medium

---

## H2 — Match between system and real world

### P2.1 — Technical error messages exposed to user

**Anti-pattern:** Raw error objects, HTTP status codes, or stack traces shown in UI.

```jsx
// BAD
setError(err.message); // might render "TypeError: Cannot read property..."
// BAD
if (res.status === 500) setError("Error 500");
```

**Fix:** Map all error conditions to user-readable strings with a recovery action.
**Heuristic:** H2 | **Norman:** N2-Signifiers | **Severity:** High

---

### P2.2 — Camel/snake case labels

**Anti-pattern:** Field labels or column headers using internal naming conventions.

```jsx
// BAD
<label>userId</label>
<th>created_at</th>
<label>recordType</label>
```

**Fix:** Use human-readable labels: "User", "Created", "Record type"
**Heuristic:** H2 | **Norman:** N2-Signifiers | **Severity:** Medium

---

### P2.3 — Icon-only buttons without accessible labels

**Anti-pattern:** Interactive icon buttons with no `aria-label`, `title`, or visible text label.

```jsx
// BAD
<button onClick={handleDelete}><TrashIcon /></button>

// GOOD
<button onClick={handleDelete} aria-label="Delete item">
  <TrashIcon />
</button>
```

**Look for:** `<button>` or `<a>` containing only an icon component with no text, no `aria-label`,
no `title`.
**Heuristic:** H2, H7 | **Norman:** N2-Signifiers | **Severity:** High

---

## H3 — User control and freedom

### P3.1 — Wizard / multi-step flow missing Back button

**Anti-pattern:** Step component with only a Next/Submit action and no Back.

```jsx
// BAD
<WizardStep>
  <button onClick={nextStep}>Next</button>
</WizardStep>
```

**Look for:** Step/wizard components with `nextStep` handler but no `prevStep` or `onBack`.
**Heuristic:** H3 | **Norman:** N6-Constraints | **Severity:** High

---

### P3.2 — Destructive action without confirmation

**Anti-pattern:** Delete, clear, or reset handlers that execute immediately without confirm dialog.

```jsx
// BAD
<button onClick={() => deleteRecord(id)}>Delete</button>

// GOOD
<button onClick={() => setShowConfirm(true)}>Delete</button>
<ConfirmDialog
  onConfirm={() => deleteRecord(id)}
  message="Delete this record? This cannot be undone."
/>
```

**Look for:** `delete`, `remove`, `clear`, `reset`, `destroy` functions called directly from
onClick with no intermediate confirmation state.
**Heuristic:** H3, H5 | **Norman:** N6-Constraints | **Severity:** Critical

---

### P3.3 — Modal with no escape/cancel

**Anti-pattern:** Modal or Dialog component missing close button, Escape key handler, or
backdrop click dismiss.

```jsx
// BAD
<Modal isOpen={open}>
  <form onSubmit={handleSubmit}>...</form>
  // no X button, no onClose prop used
</Modal>
```

**Look for:** Modal/Dialog components with no `onClose`, no close button, no `onKeyDown` for
Escape.
**Heuristic:** H3 | **Norman:** N6-Constraints | **Severity:** High

---

## H4 — Consistency and standards

### P4.1 — Inconsistent action naming

**Anti-pattern:** The same semantic action uses different labels across components.
**Look for:** Multiple labels for "save" (Save, Update, Apply, Confirm, OK), "delete" (Delete,
Remove, Discard, Clear), "cancel" (Cancel, Close, Back, Dismiss) used interchangeably.
**Strategy:** `grep -r "Delete\|Remove\|Discard\|Clear" src/ --include="*.jsx"` — check if
these are used for the same action type.
**Heuristic:** H4 | **Norman:** N4-Conceptual model | **Severity:** Medium

---

### P4.2 — Inconsistent button variants for same action type

**Anti-pattern:** Primary action styled differently across pages (sometimes `variant="primary"`,
sometimes `variant="contained"`, sometimes custom class).
**Look for:** Primary CTA buttons with inconsistent variant props or class names.
**Heuristic:** H4 | **Norman:** N4-Conceptual model | **Severity:** Medium

---

## H5 — Error prevention

### P5.1 — Form validation only on submit (not inline)

**Anti-pattern:** Validation errors that only appear after the full form is submitted.

```jsx
// BAD
const handleSubmit = (e) => {
  e.preventDefault();
  const errors = validateAll(formData); // only runs on submit
  setErrors(errors);
};
```

**Fix:** Add `onBlur` validation per field. Show constraints before user tries (H5: show
password requirements before entry, not after failure).
**Heuristic:** H5 | **Norman:** N6-Constraints | **Severity:** High

---

### P5.2 — Missing input type constraints

**Anti-pattern:** Using `type="text"` for numeric, email, phone, or date fields.

```jsx
// BAD
<input type="text" name="phone" />
<input type="text" name="email" />

// GOOD
<input type="tel" name="phone" />
<input type="email" name="email" />
```

**Look for:** Input fields named `email`, `phone`, `tel`, `zip`, `postal`, `date`, `amount`,
`price`, `count` that have `type="text"`.
**Heuristic:** H5 | **Norman:** N6-Constraints | **Severity:** Medium

---

### P5.3 — Adjacent destructive and primary actions

**Anti-pattern:** Destructive buttons (delete, reset, cancel) placed adjacent to primary
action buttons with no visual differentiation.

```jsx
// BAD
<div className="actions">
  <button>Save</button>
  <button>Delete All</button>
</div>
```

**Fix:** Visually separate destructive actions. Use color (red/danger variant) and spatial
separation (different area of the screen, not side-by-side).
**Heuristic:** H5 | **Norman:** N6-Constraints | **Severity:** High

---

## H6 — Recognition rather than recall

### P6.1 — Empty form on validation error

**Anti-pattern:** Form that clears all fields when a submission error occurs.
**Look for:** Error handling that calls `reset()` or clears form state when a server error occurs.
**Heuristic:** H6 | **Norman:** N4-Conceptual model | **Severity:** Critical

---

### P6.2 — Dropdown options showing only IDs or codes

**Anti-pattern:** Select options rendering raw IDs or codes without human-readable labels.

```jsx
// BAD
options.map((o) => <option value={o.id}>{o.id}</option>);

// GOOD
options.map((o) => <option value={o.id}>{o.name}</option>);
```

**Heuristic:** H6 | **Norman:** N2-Signifiers | **Severity:** High

---

### P6.3 — Multi-step flow that doesn't carry context forward

**Anti-pattern:** Step 3 of a wizard doesn't show summary of choices made in steps 1–2.
**Look for:** Wizard/stepper components where later steps don't reference or display earlier
selections.
**Heuristic:** H6 | **Norman:** N4-Conceptual model | **Severity:** Medium

---

## H7 — Flexibility and efficiency

### P7.1 — No keyboard shortcuts for frequent actions

**Anti-pattern:** High-frequency actions (save, search, navigate) with no keyboard shortcut.
**Look for:** Absence of `useHotkeys`, `keyboardShortcut`, `onKeyDown` handlers for Save,
Search, New, and navigation actions in productivity or enterprise tools.
**Heuristic:** H7 | **Norman:** N1-Affordances | **Severity:** Medium (High for power-user tools)

---

### P7.2 — No bulk actions on list views

**Anti-pattern:** List or table with no multi-select or bulk action capability.
**Look for:** Tables/lists where the common workflow is apply-same-action-to-many with no
checkbox column or bulk action bar.
**Heuristic:** H7 | **Norman:** N1-Affordances | **Severity:** Medium

---

## H8 — Aesthetic and minimalist design

### P8.1 — Excessive visible form fields

**Anti-pattern:** Form with >15 fields all visible simultaneously with no progressive disclosure.
**Look for:** Long forms without sections, accordions, or progressive reveal patterns.
**Heuristic:** H8 | **Norman:** N4-Conceptual model | **Severity:** Medium

---

### P8.2 — No visual hierarchy — multiple equal-weight CTAs

**Anti-pattern:** Screen with 3+ buttons at the same visual weight (same size, same variant).

```jsx
// BAD — three primary buttons, no hierarchy
<button className="btn-primary">Save</button>
<button className="btn-primary">Save and Continue</button>
<button className="btn-primary">Export</button>
```

**Heuristic:** H8 | **Norman:** N5-Mapping | **Severity:** High

---

## H9 — Error recovery

### P9.1 — Generic catch-all error message

**Anti-pattern:** Single generic error for all failure conditions.

```jsx
// BAD
catch (err) {
  setError('Something went wrong. Please try again.');
}
```

**Fix:** Handle known error types specifically. At minimum, distinguish: network errors,
validation errors, auth errors, and server errors.
**Heuristic:** H9 | **Norman:** N2-Signifiers | **Severity:** High

---

### P9.2 — Error dismissal clears form

**Anti-pattern:** Error toast/banner dismiss handler that also resets form state.
**Look for:** `onClose` or `onDismiss` handlers on error components that call form `reset()`.
**Heuristic:** H9 | **Norman:** N3-Feedback | **Severity:** Critical

---

### P9.3 — Error shown at top of page, not near field

**Anti-pattern:** Form-level error banner that doesn't scroll to or identify the offending field.

```jsx
// BAD
{
  error && <div className="error-banner">{error}</div>;
}
// ... 30 fields later ...
```

**Fix:** Show errors inline, adjacent to the field. If a top-of-page summary is needed,
also show errors inline, and auto-scroll to first error.
**Heuristic:** H9 | **Norman:** N5-Mapping | **Severity:** High

---

## H10 — Help and documentation

### P10.1 — Empty state with no instruction

**Anti-pattern:** Empty list/table that renders nothing or just "No data found".

```jsx
// BAD
{
  items.length === 0 && <p>No items found.</p>;
}

// GOOD
{
  items.length === 0 && (
    <EmptyState
      icon={<ListIcon />}
      title="No items yet"
      description="Create your first item to get started."
      action={<button onClick={handleCreate}>Create item</button>}
    />
  );
}
```

**Heuristic:** H10 | **Norman:** N2-Signifiers | **Severity:** Medium

---

### P10.2 — Complex config fields with no help text

**Anti-pattern:** Input fields for technical configuration (API keys, regex, webhook URLs,
cron expressions) with no adjacent helper text, tooltip, or example.
**Look for:** Inputs named: `apiKey`, `webhookUrl`, `cronExpression`, `regex`, `connectionString`,
`secretKey`, `token`, `endpoint` — with no `helperText`, `hint`, `description`, or `tooltip` prop.
**Heuristic:** H10 | **Norman:** N2-Signifiers | **Severity:** High

---

## Accessibility patterns (cross-heuristic)

These don't map to a single heuristic but violate multiple simultaneously:

### PA.1 — Missing ARIA roles on custom interactive components

**Look for:** `<div onClick={...}>` or `<span onClick={...}>` without `role="button"`,
`tabIndex`, and keyboard event handlers. Also: custom select/dropdown components without
`role="listbox"` / `role="option"`.
**Heuristics:** H1, H7 | **Norman:** N1-Affordances | **Severity:** High

### PA.2 — Form inputs missing associated labels

**Look for:** `<input>` without `<label htmlFor>`, `aria-label`, or `aria-labelledby`.
**Heuristics:** H2, H6 | **Norman:** N2-Signifiers | **Severity:** High

### PA.3 — Color as only differentiator

**Look for:** Error states, required fields, or status indicators that use only color (red text,
green border) with no icon, text, or pattern to communicate the same information.
**Heuristics:** H1, H5 | **Norman:** N2-Signifiers | **Severity:** Medium
