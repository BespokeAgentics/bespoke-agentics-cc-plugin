---
type: checklist
kind: go-live
project: {{project}}
ship: {{ship}}
generated: {{today}}
---

# Go-live checklist — {{project}}

Ship means: {{ship_definition}}

🟢 present and verified · 🟡 present but stale / thin / unverified · 🔴 missing · ⚪ not applicable

## A · Repository hygiene

| Item | Grade | Verified by | Task | Size |
|---|---|---|---|---|
{{hygiene_rows}}

## B · Documentation

| Item | Grade | Verified by | Task | Size |
|---|---|---|---|---|
{{docs_rows}}

### Known limitations (from Disable rows — paste into the README)

{{known_limitations}}

### Roadmap (from Defer rows — paste into the README)

{{roadmap}}

## C · Release mechanics

| Item | Grade | Verified by | Task | Size |
|---|---|---|---|---|
{{release_rows}}

### Release procedure

```bash
{{release_commands}}
```

Rollback: {{rollback}}

## D · Demo assets

| Item | Grade | Verified by | Task | Size |
|---|---|---|---|---|
{{demo_rows}}

## Not verified

{{unverified}}
