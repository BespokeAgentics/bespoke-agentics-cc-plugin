# Spec template

Write the final spec at the user-provided path (default `spec.md`) using this scaffold. Sections that the interview didn't cover should be marked `TODO — not yet elicited` rather than fabricated.

```markdown
# [Feature/Product Name]

**Created:** [timestamp]
**Status:** Draft | Review | Approved
**Version:** 1.0

---

## Executive Summary

[2–3 sentence overview of what this is and why it exists]

---

## Target Users & Scale

### Primary Users

[Who is this for — be specific]

### Scale Expectations

- Launch: [specific numbers]
- Year 1: [specific numbers]
- Long-term: [specific numbers]

### Geographic & Regulatory Context

[Where will this operate? What regulations apply?]

---

## Core Functionality

### User Stories

1. As a [role], I want to [action] so that [outcome]
2. As a [role], I want to [action] so that [outcome]
   [...]

### Primary Workflows

[Detailed workflow descriptions for main use cases]

### Business Rules

| Rule | Description | Enforced By |
| ---- | ----------- | ----------- |
| [Name] | [What it does] | [How/where enforced] |

---

## Technical Architecture

### Data Model

[Entity descriptions, relationships, constraints]

### Integration Points

| System | Purpose | Protocol | Failure Mode |
| ------ | ------- | -------- | ------------ |
| [Name] | [Why] | [How] | [What if fails] |

### State Management

[Where state lives, how it syncs, consistency guarantees]

### Performance Requirements

| Metric | Requirement | Degradation Behavior |
| ------ | ----------- | -------------------- |
| Latency | [target] | [what happens if exceeded] |
| Throughput | [target] | [what happens if exceeded] |

---

## Security & Compliance

### Authentication & Authorization

[How users prove identity, what they can access]

### Data Classification

| Data Type | Classification | Encryption | Retention |
| --------- | -------------- | ---------- | --------- |
| [Type] | [Level] | [At rest/transit] | [Duration] |

### Audit Requirements

[What gets logged, for how long, who can access]

---

## Edge Cases & Error Handling

### Known Edge Cases

| Scenario | Expected Behavior | Recovery Path |
| -------- | ----------------- | ------------- |
| [What if] | [Then] | [How to recover] |

### Error States

[How errors are communicated, retry strategies, fallbacks]

---

## UX Considerations

### Key Screens / Components

[What the user sees, navigation flow]

### Notification Strategy

| Event | Channel | Timing | Content |
| ----- | ------- | ------ | ------- |
| [Trigger] | [Email/Push/etc.] | [When] | [Template] |

---

## Future Considerations

### Extension Points

[Where this might grow, design decisions that enable flexibility]

### Migration Strategy

[How to evolve if requirements change]

### Out of Scope (Explicitly)

[What we are NOT building — be clear]

---

## Assumptions & Open Questions

### Assumptions Made

1. [Assumption 1 and rationale]
2. [Assumption 2 and rationale]

### Resolved Questions

| Question | Decision | Rationale |
| -------- | -------- | --------- |
| [Q] | [Answer] | [Why] |

---

## References

- [Link to related docs]
- [Previous discussions]
- [Similar implementations]

---

_This specification was generated through interview-driven development._
```
