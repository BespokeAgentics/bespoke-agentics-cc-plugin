# Interview dimensions

Use `AskUserQuestion` to systematically explore every dimension below. Within each dimension, the bulleted questions are the *starting* points — follow-ups are expected.

## Target & Scope

- **User Scale** — Who is this for? Hobbyists, professionals, enterprise?
- **Volume** — How many users / transactions / records at launch? At scale?
- **Geographic Scope** — Single region or global? Regulatory implications?
- **Out of Scope** — What are we explicitly *not* building? (Capture this for the final spec.)

## Technical Architecture

- **Data Model** — What entities? Relationships? Constraints?
- **Integration Points** — External APIs? Third-party services? Webhooks?
- **State Management** — Where does state live? How does it synchronize?
- **Persistence** — What must be stored? Retention policies? Backup needs?

## User Experience

- **Primary Workflows** — What are the 3 most important user journeys?
- **Access Patterns** — How do users discover and navigate features?
- **Notifications** — What events require user attention? Channels?
- **Error States** — How are failures communicated?

## Business Logic

- **Rules & Constraints** — What are the business rules? Who enforces them?
- **Edge Cases** — What happens at boundaries? Zero state? Maximum load?
- **Automation Boundaries** — What's automated vs manual? Why?
- **Rollback & Recovery** — How do you undo mistakes?

## Performance & Reliability

- **Latency Expectations** — What response times are acceptable?
- **Availability Requirements** — 99.9%? Maintenance windows?
- **Degradation Strategy** — What fails gracefully? What's critical path?
- **Observability** — What metrics matter? What logs are essential?

## Security & Compliance

- **Authentication** — Who can access? How do they prove identity?
- **Authorization** — What can each role do? Least privilege?
- **Data Sensitivity** — PII? Financial? Health data? Encryption needs?
- **Audit Requirements** — What actions need logging? Retention?

## Future Considerations

- **Extension Points** — Where might this grow? Design for flexibility?
- **Migration Path** — If requirements change, how do you evolve?
- **Deprecation Strategy** — How would you retire this?

## Coverage check

Before moving to Phase 4 (spec generation), confirm every dimension above has at least one specific, non-hand-wavy answer. Sections still vague → return to Phase 2 and probe.
