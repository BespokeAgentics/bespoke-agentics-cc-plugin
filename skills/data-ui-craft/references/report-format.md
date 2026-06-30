# Report Format — markdown + HTML

The audit emits **both** by default: `./data-ui-craft-audit.md` (in-repo, diff-friendly) and
`./data-ui-craft-audit.html` (self-contained, shareable). Same findings, two renderings. The color
system matches the plugin's `ux-audit` skill so reports look native side by side.

## Severity color system

| Level | Background | Border | Label color |
|---|---|---|---|
| Critical | `#FEF2F2` | `#F87171` | `#991B1B` |
| High | `#FFF7ED` | `#FB923C` | `#9A3412` |
| Medium | `#FFFBEB` | `#FBBF24` | `#92400E` |
| Low | `#F0FDF4` | `#4ADE80` | `#166534` |
| Opportunity | `#EFF6FF` | `#60A5FA` | `#1D4ED8` |

Pillar tags in findings: **P1** Data-driven form · **P2** Progressive disclosure · **P3** Invisible
UI. Always pair the rule ID (e.g. `DF1`, `PD2`, `IU4`) with the `file:line`.

---

## Markdown template (`data-ui-craft-audit.md`)

```markdown
# Data-UI Craft Audit — {product/surface} · {YYYY-MM-DD}

**Scope:** {files/dirs} · **Stack:** {framework + styling + data layer}
**Findings:** {n} Critical · {n} High · {n} Medium · {n} Low · {n} Opportunities

## Executive summary
{3–5 sentences for a PM, not a dev. Lead with user impact, not rule names. Name the single
highest-impact finding and the single best opportunity. End with one recommended first action.}

## Surfaces analyzed
- `path/Table.tsx:30` — Users table — cols: name(text), email(id), dept(categorical),
  status(status), seats(numeric), lastSeen(datetime); actions: edit, deactivate, remove.

## Findings
### 🔴 Critical
- **[DF1 · P1]** `EarningsTable.tsx:88` — Revenue/EPS columns are left-aligned with ragged
  decimals, so the core comparison the page exists for can't be done at a glance. *Fix:* right-align
  + `tabular-nums` + one `Intl` currency format (12 instances, column-def change).

### 🟠 High
- **[IU4 · P3]** `Dashboard.tsx:142` — The main table renders a bare frame when empty; first-time
  users see what looks like a broken page. *Fix:* `EmptyState` with a "Create your first…" action.

### 🟡 Medium
- …

### 🟢 Low
- …

## Opportunities
- **[DF6 · P1]** `Activity.tsx:50` — The 30-row timestamp column is scanned for trends; a sparkline
  above the table would answer it in one glance. (Low effort, uses existing Recharts.)

## Recommended order
1. {Critical fixes} 2. {High} 3. {quick-win Low/Medium} 4. {opt-in Opportunities}

## Next step
Run `/bespokeagentics:data-ui-craft implement {scope}` to apply the accepted set.
```

---

## HTML template (`data-ui-craft-audit.html`)

Self-contained, inline styles, no dependencies. Fill the `<!-- … -->` sections. Reuse this exact
skeleton (collapsible finding cards + summary grid).

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Data-UI Craft Audit</title>
<style>
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  :root{
    --crit-bg:#fef2f2;--crit-bd:#f87171;--crit-tx:#991b1b;
    --high-bg:#fff7ed;--high-bd:#fb923c;--high-tx:#9a3412;
    --med-bg:#fffbeb;--med-bd:#fbbf24;--med-tx:#92400e;
    --low-bg:#f0fdf4;--low-bd:#4ade80;--low-tx:#166534;
    --opp-bg:#eff6ff;--opp-bd:#60a5fa;--opp-tx:#1d4ed8;
    --font:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  }
  @media (prefers-color-scheme:dark){
    body{background:#111827;color:#f9fafb}
    .card,.summary-card,.executive{background:#1f2937;border-color:#374151}
    code,pre{background:#374151;color:#e5e7eb}
    th{background:#1f2937!important}
  }
  body{font-family:var(--font);font-size:14px;line-height:1.6;background:#f9fafb;color:#111827;padding:2rem}
  .container{max-width:960px;margin:0 auto}
  h1{font-size:24px;font-weight:600}
  h2{font-size:18px;font-weight:600;margin:2rem 0 1rem}
  .meta{font-size:12px;color:#6b7280;margin-bottom:1.5rem}
  .summary-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:1.5rem}
  .summary-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:12px;text-align:center}
  .summary-card .count{font-size:28px;font-weight:700}
  .summary-card .label{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-top:2px}
  .executive{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:1.25rem;margin-bottom:1.5rem;line-height:1.7}
  .card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:12px;overflow:hidden}
  .card-header{padding:14px 16px;cursor:pointer;display:flex;align-items:flex-start;gap:12px;user-select:none}
  .card-header:hover{background:#f9fafb}
  .pill{font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px;white-space:nowrap;flex-shrink:0;margin-top:2px}
  .pill-crit{background:var(--crit-bg);color:var(--crit-tx);border:1px solid var(--crit-bd)}
  .pill-high{background:var(--high-bg);color:var(--high-tx);border:1px solid var(--high-bd)}
  .pill-med{background:var(--med-bg);color:var(--med-tx);border:1px solid var(--med-bd)}
  .pill-low{background:var(--low-bg);color:var(--low-tx);border:1px solid var(--low-bd)}
  .pill-opp{background:var(--opp-bg);color:var(--opp-tx);border:1px solid var(--opp-bd)}
  .card-title{font-weight:600;font-size:14px;flex:1}
  .card-sub{font-size:12px;color:#6b7280;margin-top:2px}
  .card-body{padding:0 16px 16px;border-top:1px solid #f3f4f6;display:none}
  .card-body.open{display:block}
  .card-body section{margin-top:14px}
  .card-body h4{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#9ca3af;margin-bottom:6px}
  .loc{font-size:12px;color:#6b7280;background:#f3f4f6;border-radius:4px;padding:6px 10px;font-family:monospace}
  code{background:#f3f4f6;border-radius:3px;padding:1px 5px;font-family:Consolas,monospace;font-size:12px}
  pre{background:#1f2937;color:#e5e7eb;border-radius:6px;padding:12px;overflow-x:auto;font-size:12px;line-height:1.5;margin-top:6px}
  .fix{background:#f0fdf4;border-left:3px solid #4ade80;border-radius:0 6px 6px 0;padding:10px 12px;margin-top:8px}
  .fix p{color:#166534;font-size:13px}
  table{width:100%;border-collapse:collapse;margin-bottom:1.5rem;background:#fff;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden}
  th{background:#f9fafb;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#6b7280;padding:10px 14px;text-align:left;border-bottom:1px solid #e5e7eb}
  td{padding:10px 14px;border-bottom:1px solid #f3f4f6;font-size:13px;vertical-align:top}
  .chevron{margin-left:auto;color:#9ca3af;transition:transform .2s}
  .chevron.open{transform:rotate(90deg)}
  .methodology{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:1rem 1.25rem;margin-top:2rem;font-size:12px;color:#6b7280}
</style>
</head>
<body>
<div class="container">
  <h1>Data-UI Craft Audit</h1>
  <div class="meta"><!-- {surface} · {date} · {N files / N surfaces} · {stack} --></div>

  <div class="summary-grid">
    <div class="summary-card"><div class="count" style="color:#991B1B"><!--N--></div><div class="label">Critical</div></div>
    <div class="summary-card"><div class="count" style="color:#9A3412"><!--N--></div><div class="label">High</div></div>
    <div class="summary-card"><div class="count" style="color:#92400E"><!--N--></div><div class="label">Medium</div></div>
    <div class="summary-card"><div class="count" style="color:#166534"><!--N--></div><div class="label">Low</div></div>
    <div class="summary-card"><div class="count" style="color:#1D4ED8"><!--N--></div><div class="label">Opportunities</div></div>
  </div>

  <div class="executive"><!-- 3–5 sentence summary: user-impact first, top finding, best opportunity, recommended first action --></div>

  <h2>All findings</h2>
  <table>
    <thead><tr><th>#</th><th>Severity</th><th>Pillar</th><th>Rule</th><th>Finding</th><th>Location</th></tr></thead>
    <tbody>
      <!-- <tr><td>1</td><td><span class="pill pill-crit">Critical</span></td><td>P1</td><td>DF1</td>
           <td>Revenue column left-aligned</td><td><code>EarningsTable.tsx:88</code></td></tr> -->
    </tbody>
  </table>

  <h2>Finding details</h2>
  <div id="findings">
    <!-- Repeat per finding:
    <div class="card">
      <div class="card-header" onclick="toggle(this)">
        <span class="pill pill-crit">Critical</span>
        <div><div class="card-title">Revenue column can't be compared at a glance</div>
             <div class="card-sub">EarningsTable.tsx:88 · P1 Data-driven form · DF1</div></div>
        <span class="chevron">›</span>
      </div>
      <div class="card-body">
        <section><h4>What the user experiences</h4><p>…</p></section>
        <section><h4>Location</h4><div class="loc">EarningsTable.tsx · line 88 · revenue column</div></section>
        <section><h4>Before</h4><pre><code>&lt;td&gt;{row.revenue}&lt;/td&gt;</code></pre></section>
        <section><h4>Fix</h4><div class="fix"><p>Right-align + tabular-nums + one Intl currency format; apply on the column def (12 instances).</p></div>
          <pre><code>&lt;td className="text-right tabular-nums"&gt;{usd.format(row.revenue)}&lt;/td&gt;</code></pre></section>
      </div>
    </div> -->
  </div>

  <h2>Opportunities</h2>
  <div id="opportunities"><!-- same card markup with class pill-opp --></div>

  <div class="methodology"><strong>Methodology:</strong>
    <!-- files/surfaces reviewed; stack detected; framework: Data-UI Craft 3-pillar rule set (DF/PD/IU); skill version --></div>
</div>
<script>
  function toggle(h){const b=h.nextElementSibling,c=h.querySelector(".chevron");
    const open=b.classList.toggle("open");c.classList.toggle("open",open);}
</script>
</body>
</html>
```

## Writing guidelines

- **Executive summary:** for a PM. Lead with impact ("first-time users see a blank page that looks
  broken"), not labels ("IU4 violation").
- **Finding titles:** describe the user experience, not the code symptom. Good: "Numbers in the
  revenue column can't be compared at a glance." Bad: "Missing `text-right` on `<td>`."
- **Fix specificity:** exact change + before/after when possible, and note if it's a one-shot
  column-def change vs per-row.
- **Opportunities are genuine:** good patterns to amplify, or high-value low-effort wins — not filler.
