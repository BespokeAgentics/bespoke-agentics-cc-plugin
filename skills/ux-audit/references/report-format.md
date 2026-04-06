# Report Format Reference

Generate a self-contained HTML report. All styles are inline — no external dependencies.
Save to `/mnt/user-data/outputs/ux-audit-report.html`.

---

## Severity color system

| Level       | Background | Border  | Label color |
| ----------- | ---------- | ------- | ----------- |
| Critical    | #FEF2F2    | #F87171 | #991B1B     |
| High        | #FFF7ED    | #FB923C | #9A3412     |
| Medium      | #FFFBEB    | #FBBF24 | #92400E     |
| Low         | #F0FDF4    | #4ADE80 | #166534     |
| Opportunity | #EFF6FF    | #60A5FA | #1D4ED8     |

Dark mode: invert lightness — use dark bg variants (#1F2937 for dark bg, lighter text).

---

## HTML Report Template

Use this structure. Fill in the variable sections marked with `<!-- ... -->`.

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>UX Audit Report</title>
    <style>
      *,
      *::before,
      *::after {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }
      :root {
        --c-critical-bg: #fef2f2;
        --c-critical-border: #f87171;
        --c-critical-text: #991b1b;
        --c-high-bg: #fff7ed;
        --c-high-border: #fb923c;
        --c-high-text: #9a3412;
        --c-medium-bg: #fffbeb;
        --c-medium-border: #fbbf24;
        --c-medium-text: #92400e;
        --c-low-bg: #f0fdf4;
        --c-low-border: #4ade80;
        --c-low-text: #166534;
        --c-opp-bg: #eff6ff;
        --c-opp-border: #60a5fa;
        --c-opp-text: #1d4ed8;
        --font: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      @media (prefers-color-scheme: dark) {
        body {
          background: #111827;
          color: #f9fafb;
        }
        .card {
          background: #1f2937;
          border-color: #374151;
        }
        .summary-card {
          background: #1f2937;
        }
        code {
          background: #374151;
          color: #e5e7eb;
        }
        .findings-table th {
          background: #1f2937;
        }
        .findings-table td {
          border-color: #374151;
        }
      }
      body {
        font-family: var(--font);
        font-size: 14px;
        line-height: 1.6;
        background: #f9fafb;
        color: #111827;
        padding: 2rem;
      }
      .container {
        max-width: 960px;
        margin: 0 auto;
      }
      h1 {
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 4px;
      }
      h2 {
        font-size: 18px;
        font-weight: 600;
        margin: 2rem 0 1rem;
      }
      h3 {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 6px;
      }
      .meta {
        font-size: 12px;
        color: #6b7280;
        margin-bottom: 2rem;
      }
      .summary-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin-bottom: 2rem;
      }
      .summary-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
      }
      .summary-card .count {
        font-size: 28px;
        font-weight: 700;
      }
      .summary-card .label {
        font-size: 11px;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 2px;
      }
      .executive-summary {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 2rem;
        line-height: 1.7;
      }
      .card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        margin-bottom: 12px;
        overflow: hidden;
      }
      .card-header {
        padding: 14px 16px;
        cursor: pointer;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        user-select: none;
      }
      .card-header:hover {
        background: #f9fafb;
      }
      .severity-pill {
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 20px;
        white-space: nowrap;
        flex-shrink: 0;
        margin-top: 2px;
      }
      .pill-critical {
        background: var(--c-critical-bg);
        color: var(--c-critical-text);
        border: 1px solid var(--c-critical-border);
      }
      .pill-high {
        background: var(--c-high-bg);
        color: var(--c-high-text);
        border: 1px solid var(--c-high-border);
      }
      .pill-medium {
        background: var(--c-medium-bg);
        color: var(--c-medium-text);
        border: 1px solid var(--c-medium-border);
      }
      .pill-low {
        background: var(--c-low-bg);
        color: var(--c-low-text);
        border: 1px solid var(--c-low-border);
      }
      .pill-opp {
        background: var(--c-opp-bg);
        color: var(--c-opp-text);
        border: 1px solid var(--c-opp-border);
      }
      .card-title {
        font-weight: 600;
        font-size: 14px;
        flex: 1;
      }
      .card-subtitle {
        font-size: 12px;
        color: #6b7280;
        margin-top: 2px;
      }
      .heuristic-tag {
        font-size: 11px;
        color: #6b7280;
        flex-shrink: 0;
        margin-top: 2px;
      }
      .card-body {
        padding: 0 16px 16px;
        border-top: 1px solid #f3f4f6;
        display: none;
      }
      .card-body.open {
        display: block;
      }
      .card-body section {
        margin-top: 14px;
      }
      .card-body section h4 {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #9ca3af;
        margin-bottom: 6px;
      }
      .card-body p {
        font-size: 13px;
        color: #374151;
        line-height: 1.6;
      }
      .location {
        font-size: 12px;
        color: #6b7280;
        background: #f3f4f6;
        border-radius: 4px;
        padding: 6px 10px;
        font-family: monospace;
        margin-top: 4px;
      }
      code {
        background: #f3f4f6;
        border-radius: 3px;
        padding: 1px 5px;
        font-family: "SFMono-Regular", Consolas, monospace;
        font-size: 12px;
      }
      pre {
        background: #1f2937;
        color: #e5e7eb;
        border-radius: 6px;
        padding: 12px;
        overflow-x: auto;
        font-size: 12px;
        line-height: 1.5;
        margin-top: 6px;
      }
      .fix-box {
        background: #f0fdf4;
        border-left: 3px solid #4ade80;
        border-radius: 0 6px 6px 0;
        padding: 10px 12px;
        margin-top: 8px;
      }
      .fix-box p {
        color: #166534;
        font-size: 13px;
      }
      .findings-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 2rem;
        background: white;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
      }
      .findings-table th {
        background: #f9fafb;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6b7280;
        padding: 10px 14px;
        text-align: left;
        border-bottom: 1px solid #e5e7eb;
      }
      .findings-table td {
        padding: 10px 14px;
        border-bottom: 1px solid #f3f4f6;
        font-size: 13px;
        vertical-align: top;
      }
      .chevron {
        font-size: 12px;
        color: #9ca3af;
        transition: transform 0.2s;
        margin-left: auto;
      }
      .chevron.open {
        transform: rotate(90deg);
      }
      .methodology {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-top: 2rem;
        font-size: 12px;
        color: #6b7280;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>UX Audit Report</h1>
      <div class="meta">
        <!-- Insert: "Audited: [product/component name] · [date] · [N files / N video frames]" -->
      </div>

      <!-- SUMMARY GRID -->
      <div class="summary-grid">
        <div class="summary-card">
          <div class="count" style="color: #991B1B;"><!-- N --></div>
          <div class="label">Critical</div>
        </div>
        <div class="summary-card">
          <div class="count" style="color: #9A3412;"><!-- N --></div>
          <div class="label">High</div>
        </div>
        <div class="summary-card">
          <div class="count" style="color: #92400E;"><!-- N --></div>
          <div class="label">Medium</div>
        </div>
        <div class="summary-card">
          <div class="count" style="color: #166534;"><!-- N --></div>
          <div class="label">Low</div>
        </div>
        <div class="summary-card">
          <div class="count" style="color: #1D4ED8;"><!-- N --></div>
          <div class="label">Opportunities</div>
        </div>
      </div>

      <!-- EXECUTIVE SUMMARY -->
      <div class="executive-summary">
        <!-- 3–5 sentence narrative summary. Cover: overall UX health, most impactful finding,
         most impactful opportunity. End with one recommended first action. -->
      </div>

      <!-- FINDINGS TABLE (overview) -->
      <h2>All findings</h2>
      <table class="findings-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Severity</th>
            <th>Finding</th>
            <th>Heuristic</th>
            <th>Norman</th>
            <th>Location</th>
          </tr>
        </thead>
        <tbody>
          <!-- One row per finding. Example:
      <tr>
        <td>1</td>
        <td><span class="severity-pill pill-critical">Critical</span></td>
        <td>Destructive action with no confirmation</td>
        <td>H3, H5</td>
        <td>N6 Constraints</td>
        <td><code>RecordList.jsx:142</code></td>
      </tr>
      -->
        </tbody>
      </table>

      <!-- FINDINGS DETAIL (expandable) -->
      <h2>Finding details</h2>
      <div id="findings">
        <!-- Repeat this card block for each finding. Example:

    <div class="card">
      <div class="card-header" onclick="toggle(this)">
        <span class="severity-pill pill-critical">Critical</span>
        <div>
          <div class="card-title">Destructive delete with no confirmation</div>
          <div class="card-subtitle">RecordList.jsx · H3 User control · N6 Constraints</div>
        </div>
        <span class="chevron">›</span>
      </div>
      <div class="card-body">
        <section>
          <h4>What the user experiences</h4>
          <p>Clicking the trash icon immediately deletes the record with no confirmation.
             Users who click accidentally have no recovery path.</p>
        </section>
        <section>
          <h4>Location</h4>
          <div class="location">RecordList.jsx · Line 142 · deleteRecord() handler</div>
        </section>
        <section>
          <h4>Code causing the issue</h4>
          <pre><code>&lt;button onClick={() => deleteRecord(id)}&gt;
  &lt;TrashIcon /&gt;
&lt;/button&gt;</code></pre>
        </section>
        <section>
          <h4>Recommended fix</h4>
          <div class="fix-box">
            <p>Add a confirmation dialog before executing the delete. Consider a 5-second
               undo window (soft delete) instead of a hard confirm, for a better H3 experience.</p>
          </div>
          <pre><code>const [confirmId, setConfirmId] = useState(null);

&lt;button onClick={() => setConfirmId(id)}&gt;
  &lt;TrashIcon /&gt;
&lt;/button&gt;
{confirmId === id && (
  &lt;ConfirmDialog
    message="Delete this record? This cannot be undone."
    onConfirm={() => { deleteRecord(id); setConfirmId(null); }}
    onCancel={() => setConfirmId(null)}
  /&gt;
)}</code></pre>
        </section>
        <section>
          <h4>Norman diagnosis</h4>
          <p><strong>N6 — Constraints:</strong> The design places no structural barrier
             between intent and irreversible action. A constraint (confirmation step) is needed
             to prevent the error from occurring, not just to recover from it.</p>
        </section>
      </div>
    </div>

    -->
      </div>

      <!-- OPPORTUNITIES -->
      <h2>Opportunities</h2>
      <div id="opportunities">
        <!-- Same card format, use pill-opp class -->
      </div>

      <!-- METHODOLOGY -->
      <div class="methodology">
        <strong>Methodology:</strong>
        <!-- List what was analyzed:
    - Files reviewed: X .jsx files, Y .tsx files
    - Video: [filename], [duration], [N frames extracted at fps=N]
    - Framework used: Nielsen's 10 Usability Heuristics + Norman's 6 Design Principles
    - Code pattern library version: ux-audit skill v1.0
    -->
      </div>
    </div>
    <script>
      function toggle(header) {
        const body = header.nextElementSibling;
        const chev = header.querySelector(".chevron");
        const open = body.classList.toggle("open");
        chev.classList.toggle("open", open);
      }
    </script>
  </body>
</html>
```

---

## Report writing guidelines

- **Executive summary:** Write for a product manager or VP, not a developer. Avoid jargon.
  Lead with impact ("Users cannot tell if their payment was processed") not with labels
  ("Heuristic 1 violation found in PaymentForm.jsx").
- **Finding titles:** Describe the user experience, not the code symptom.
  Good: "Users can delete records without any confirmation"
  Bad: "Missing window.confirm() call on deleteRecord()"
- **Fix specificity:** Include the exact change needed. If possible, show before/after code.
  Don't say "add error handling" — say "wrap the submitPayment() call in try/catch and call
  setError() with user-readable strings for network errors, auth errors, and server errors."
- **Norman diagnosis:** For each finding, add one paragraph explaining _why_ this is a cognitive
  mismatch — which Norman principle is at the root, and what structural change would resolve it.
- **Opportunities:** These are genuine positives — good patterns worth keeping and amplifying,
  or quick wins that would provide high value with low effort. Not just "you could add dark mode."
