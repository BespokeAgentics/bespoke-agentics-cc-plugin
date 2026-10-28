# Edge cases — {target title}

> **Target:** {kind} `{spec}` · **Level:** {level}{ — degraded from prove: reason} ·
> **Date:** {YYYY-MM-DD} · **Grounded:** {yes|no} · **Built:** {yes|no|n/a}

## Verdict

{One line, chosen by the rules in references/report.md § Sections.}

| P0 | P1 | P2 | P3 | Handled | Partial | Unhandled | Unknown | Decisions needed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| {a} | {b} | {c} | {d} | {H} | {P} | {U} | {K} | {D} |

## Top risks

### EC-xx · {title} — {priority} · {severity} × {likelihood}{ · introduced | pre-existing (changes targets)}

- **Given** {given}
- **When** {when}
- **Then** {then} — *{expected_source}: {expected_evidence}*
- **Current:** {current_status} — {current_evidence} *({verification})*

{…up to five in full; then:}

Also P0/P1: EC-xx {title} · EC-xx {title}

## Decisions needed

| Case | Question | Proposed | Alternatives |
| --- | --- | --- | --- |
| EC-xx | {Given/When, as a question} | **DECISION NEEDED** — {proposal} | {alternative} · {alternative} |

## Case matrix

{paste the output of check_cases.py --markdown}

## Cases by lens

### {Lens name}

#### EC-xx · {title}

- **Given** {given} · **When** {when}
- **Then** {then}
- **Expected source:** {spec | convention | proposed (decision)} — {expected_evidence}
- **Current:** {status} — {current_evidence} · verification: {verification}
- **Priority:** {priority} ({severity} × {likelihood}) · **Stems from:** {stems_from}
- **Test idea:** {test_idea}

## Scenario walkthroughs

### W1 — {persona}, {goal}

{five to ten plain-language steps, citing case ids in order}

## Probe results

| Case | Probe file (removed) | Verdict | Output |
| --- | --- | --- | --- |
| EC-xx | `{path}` | {probe-confirmed / probe-not-reproduced / probe-inconclusive} | {the assertion or error line} |

## Coverage and limits

- **Lenses applied:** {ids}
- **Lenses skipped:** {id — reason}
- **Unknown statuses:** {K} — {what would resolve them}
- **Cut:** {trimmed at quick} · **Dropped as filler:** {n}
- **Not done at this level:** {e.g. no skeptic verification (standard) · probes declined · --no-ground}

## Dismissed

| Case | Title | Why it cannot happen here |
| --- | --- | --- |

## Appendix — test skeletons

### EC-xx · {title}

```{language}
{skeleton in the repo's own framework and idiom}
```
