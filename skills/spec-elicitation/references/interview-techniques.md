# Interview techniques

## 1. Use multi-choice questions

Structure each `AskUserQuestion` with 2–4 concrete options plus the implicit "Other" slot.

```
What creator scale are you targeting?
1. Hobbyists (<$1K/month)
2. Mid-tier ($1K–$50K/month)
3. Professional ($50K+/month)
4. All tiers (tiered product)
```

Multi-choice questions reduce ambiguity, surface assumptions, prevent hand-wavy answers, and force concrete decisions.

## 2. Ask non-obvious questions

- ❌ Bad: "What features should it have?"
- ✅ Good: "What happens when a user tries to *action* but *constraint* applies?"

- ❌ Bad: "Should it be fast?"
- ✅ Good: "A user is about to miss a deadline. They click *action*. What's the maximum wait time before they give up?"

Scenario-driven, edge-case-driven questions extract real requirements. Abstract questions extract abstract answers.

## 3. Challenge assumptions

- "You mentioned X — but what if Y happens?"
- "How does this work for users who *edge case*?"
- "What's the worst thing that could happen here?"
- "If this had to support 10× the volume tomorrow, what breaks first?"

## 4. Follow up relentlessly

Each answer should generate 1–3 follow-ups until you hit bedrock understanding. Don't accept the first answer if it's vague. Common follow-up patterns:

- "Be specific — what number?" (turn qualitative answers into quantitative)
- "Walk me through a concrete example."
- "What's the failure mode of that approach?"
- "How does this interact with [previously elicited constraint]?"

## 5. Watch for contradictions

When a new answer contradicts an earlier one, stop and reconcile. Often the second answer reveals a hidden assumption that wasn't surfaced the first time.

## 6. Surface what's *not* being built

Explicitly ask "What's out of scope?" — it's as important as what's in scope. The final spec must contain an `Out of Scope` section, and the interview is the time to populate it.
