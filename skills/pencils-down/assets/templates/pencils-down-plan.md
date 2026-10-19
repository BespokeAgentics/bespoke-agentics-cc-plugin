---
type: plan
kind: pencils-down
project: {{project}}
pencils_down: {{pencils_down}}
ship: {{ship}}
capacity: "{{capacity}}"
fits: {{fits}}
assumed_count: {{assumed_count}}
generated: {{today}}
sources: [plans, commits, wiki, interview]
---

# Pencils Down — {{project}}

## 1. The sentence

> {{value_proposition}}

Source: {{value_proposition_source}}

## 2. The dates

| | |
|---|---|
| Pencils down | {{pencils_down}} |
| Ship | {{ship}} |
| Working days remaining | {{working_days}} |
| Capacity assumed | {{capacity}} |

{{arithmetic_verdict}}

## 3. The line

After **{{pencils_down}}**, no new capability enters this project. Work permitted: the Finish rows
in § 4 until their acceptance criteria pass; the Disable and Cut rows in § 5 and § 6; every task in
`go-live-checklist.md`; the outreach in `outreach/`. Anything else is written into § 7 and waits
for the next pencils-down.

## 4. Finish

{{finish_workstreams}}

## 5. Disable

{{disable_rows}}

## 6. Cut

{{cut_rows}}

## 7. Deferred (the roadmap)

{{deferred_rows}}

## 8. Cut to fit the date

{{fit_moves}}

## 9. Go-live preparation

See `go-live-checklist.md` — 🟢 {{g}} · 🟡 {{y}} · 🔴 {{r}} · ⚪ {{na}}.

Highest-leverage tasks:

{{top_go_live_tasks}}

## 10. Outreach

{{outreach_summary}}

## 11. Assumptions

{{assumptions}}

Collector notes:

{{collector_notes}}

## 12. Appendix

### Ambiguity register

| Question | Readings | Resolved to | By |
|---|---|---|---|
{{ambiguity_rows}}

### Commits in window

{{commit_summary}}

### Plans consulted

{{plans_consulted}}
