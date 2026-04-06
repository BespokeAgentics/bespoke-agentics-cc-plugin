---
type: integration
client:
status:
system-name:
direction: # inbound|outbound|bidirectional
frequency: # real-time|batch|on-demand
auth-method:
created:
updated:
sources:
tags:
---

# Integration: [System Name]

## Overview

<!-- Provide a high-level description of this integration:
- What two systems or components are connected?
- What business process or use case does it support?
- Why is this integration needed?
- Who uses or depends on it?

Link to relevant [[entity|systems and entities]] involved.
-->

## Data Flow

<!-- Document what data flows in what direction:
- **Inbound**: What data comes FROM the external system INTO Salesforce?
  - Data types, frequency, triggering conditions
- **Outbound**: What data goes FROM Salesforce TO the external system?
  - Data types, frequency, triggering conditions
- **Error handling**: What happens if sync fails?
  - Retry logic, notifications, escalation

Use a diagram or structured format if helpful. Link to relevant [[feature|features]] that depend on this flow.
-->

## Current Implementation

<!-- Describe the current state of this integration:
- What integration tool or platform is used (e.g., middleware, API, ETL tool)?
- How is it configured and maintained?
- What has worked well and what are pain points?
- Known limitations or issues?

Link to the source [[entity|system]] and any [[meeting|discussions]] about current state.
-->

## Target Architecture

<!-- Describe how this integration should work in Salesforce:
- Integration approach (Salesforce APIs, middleware, third-party connector)?
- Data transformation or mapping logic
- Error handling and retry strategy
- Monitoring and alerting
- Scalability and performance considerations
- Security and compliance requirements

Link to related [[decision|design decisions]] and [[gap|gaps]].
-->

## Authentication & Security

<!-- Document security aspects:
- Authentication method (OAuth, API key, etc.)
- Secret management and rotation
- Encryption in transit and at rest
- Network or firewall considerations
- Compliance requirements (GDPR, SOC 2, etc.)
- Access control and audit logging

Reference any [[decision|security decisions]] made about this integration.
-->

## Error Handling

<!-- Describe how errors and failure scenarios are handled:
- Types of errors that can occur (network, validation, timeout, etc.)
- Retry logic and backoff strategy
- Logging and monitoring approach
- Alerting and escalation procedures
- Recovery and reconciliation processes
- Testing and validation approach

Link to related [[gap|gaps]] or [[question|open questions]] about error scenarios.
-->

## Dependencies

<!-- List what this integration depends on:
- [[feature|Features]] that depend on this integration
- [[entity|Systems or components]] that must be available
- [[decision|Decisions]] about architecture or approach
- Data or configuration that must be prepared
- Third-party tools or licenses required

Include sequencing notes if this integration must be built in phases.
-->

## Open Questions

<!-- List unresolved questions about this integration:
- Technical architecture decisions that need clarity
- Business process questions from stakeholders
- Performance or scalability concerns
- Security or compliance considerations

Link to related [[question|question pages]] and indicate who should provide answers.
-->
