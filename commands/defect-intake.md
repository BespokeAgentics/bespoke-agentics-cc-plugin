---
name: "bespokeagentics:defect-intake"
description: "Take a defect found mid-session through proper disposition instead of noting it and moving on. Verifies the defect is real before editing anything (an unreproduced defect is a hypothesis), classifies it by blast radius as fix-now / fold-into-current-change / escalate-to-user — never by who introduced it — records a baseline from the repo's own gates, writes the failing test first so the fix is provable, applies the narrowest fix that turns it green, re-runs the gates against the baseline, documents the symptom/root cause/fix/why-it-was-wrong where that repo keeps durable knowledge, and resumes the interrupted work with an honest account. Escalation means stopping and asking now, not a TODO or a line in a summary. A failing test is never deleted, skipped, or loosened to reach green. Never commits."
argument-hint: "<defect description, file:line, or paste of the failing output>"
allowed-tools: Skill(defect-intake), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep, Agent
---

# Defect Intake

Run the `defect-intake` skill on the defect described in the arguments: capture it concretely,
verify it is real before touching any code, classify its disposition by blast radius, baseline the
repo's gates, write the failing test first, fix narrowly, re-verify against the baseline, document
it where this repo keeps durable knowledge, and return to the interrupted work with a faithful
report of what changed and what — if anything — you are escalating.

If the arguments are empty, ask what the defect is rather than sweeping the repo for candidates;
this skill dispositions a known defect, it does not hunt for new ones.

ARGUMENTS: $ARGUMENTS
