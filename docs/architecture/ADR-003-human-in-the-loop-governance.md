# ADR 003: Human-in-the-Loop Governance and Consequential Action Safeguards

## Status
Accepted

## Context
In financial banking systems governed by regulatory compliance standards (PCI-DSS, SOC 2, SOX, FFIEC), autonomous systems must never execute destructive or consequential operations (such as rollbacks, service restarts, or certificate rotations) without explicit, authenticated human oversight and an immutable audit trail. Unchecked autonomous execution risks cascading outages, unverified data corruption, or compliance violations.

## Decision
We implemented a strict **Finite State Machine with an Enforced Human Approval Gate**:
1. State progression: `OPEN → INVESTIGATING → AWAITING_APPROVAL → REMEDIATING → VERIFYING → RESOLVED / REOPENED`.
2. The AI orchestrator can autonomously investigate, collect evidence, query telemetry, and synthesize root causes, but it is **strictly halted** at `AWAITING_APPROVAL`.
3. Remediation execution requires an authenticated `POST /api/incidents/{id}/approve` request signed by a user with the `INCIDENT_MANAGER` or `ADMIN` role.
4. Consequential remediation tools (`rollback_deployment`, `restart_service`, `rotate_ssl_certificate`) can only be invoked by the Orchestrator when the incident is explicitly in the `REMEDIATING` state.
5. All actions (investigation start, findings, approval, rejection, remediation execution, post-fix health verification) are logged into an immutable `audit_entries` table with user attribution and correlation IDs.

## Consequences
### Positive
- **Regulatory Compliance**: Satisfies change management and audit trail requirements.
- **Fail-Safe**: Human operators can review evidence, alternate hypotheses, and risk ratings before any infrastructure is touched.
- **Automated Verification**: Post-approval fixes are immediately and automatically verified; if health checks fail, the incident transitions to `REOPENED`.
