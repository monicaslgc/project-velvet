# Project Velvet

**AI-ready operational workflows for professional beauty commerce — portfolio demonstrations.**

Project Velvet explores how backend workflows can make order operations more reliable, explainable, and safe to automate. It uses synthetic data and generic business scenarios. It is not a WellaOne implementation and is not affiliated with or connected to any real commerce platform.

## Demo 1: Order Lifecycle Consistency

A deterministic policy engine evaluates order events before any downstream system acts on them. It checks required fields, duplicate event IDs, expected order versions, and allowed state transitions.

## Demo 2: Order Exception Triage

A deterministic triage policy classifies synthetic exceptions, assigns a priority, routes each known category to a responsible operational team, explains the evidence behind the decision, and flags cases for human review. Unknown categories and malformed payloads fail closed to manual review.

## Demo 3: Order Reconciliation

A read-only comparison checks two snapshots of the same order across status, total, currency, and item count. It reports every mismatch with expected and observed values, applies an illustrative severity policy, and flags high-severity discrepancies for human review. It never assumes which source is authoritative and never repairs data automatically.

## Demo 4: AI Workflow Governance

A deterministic policy evaluates proposed agent actions against explicit autonomy boundaries. Read-only inspection and internal drafts are allowed within scope; customer communication, financial transactions, order or inventory mutations, and external system changes require human approval. Invalid or unknown actions fail closed to manual review. The evaluator only returns a decision; it never executes the action or integrates with external systems.

### What this demonstrates
- Explicit business rules before AI-assisted recommendations
- Explainable classification and routing
- Fail-closed handling for invalid or unknown input
- Human review for high-risk decisions
- Reusable agent skill instructions
- Mermaid diagrams, synthetic fixtures, unit tests, and CI

### Scope boundaries
These demos are in-memory evaluators. They do **not** persist an event ledger, mutate a real order, or trigger payment, cancellation, shipment, refund, stock adjustment, or customer communication. Duplicate detection in the lifecycle demo is only against IDs supplied in the current evaluation call; production-grade idempotency requires an atomic, durable event ledger. Version checking detects conflicts but does not resolve concurrency by itself. Exception priorities and thresholds are illustrative policy choices, not claims about any real platform's operating rules.

## Quick start

Requires Python 3.11+.

```bash
python -m pip install -e ".[dev]"
pytest
python examples/run_demo.py
python examples/audit_demo.py
python examples/triage_demo.py
python examples/reconciliation_demo.py
python examples/governance_demo.py
```

## Repository map

```text
src/velvet/order_lifecycle.py
src/velvet/exception_triage.py
src/velvet/order_reconciliation.py
src/velvet/audit_trail.py
src/velvet/workflow_governance.py
examples/orders.json
examples/exceptions.json
examples/run_demo.py
examples/audit_demo.py
examples/triage_demo.py
examples/reconciliation_demo.py
examples/governance.json
examples/governance_demo.py
docs/order-lifecycle-flow.mmd
docs/order-lifecycle-states.mmd
docs/audit-trail-review-flow.mmd
docs/order-exception-triage-flow.mmd
docs/order-reconciliation-flow.mmd
docs/ai-workflow-governance-flow.mmd
skills/order-lifecycle-consistency/SKILL.md
skills/order-exception-triage/SKILL.md
skills/order-reconciliation/SKILL.md
skills/audit-trail-human-review/SKILL.md
skills/ai-workflow-governance/SKILL.md
tests/test_order_lifecycle.py
tests/test_exception_triage.py
tests/test_order_reconciliation.py
tests/test_audit_trail.py
tests/test_workflow_governance.py
.github/workflows/tests.yml
```

## Order lifecycle decision outcomes

| Outcome | Meaning |
|---|---|
| `ALLOWED` | Event passes policy; proposed next state/version are returned |
| `INVALID_INPUT` | Required event data is missing or malformed |
| `DUPLICATE_EVENT` | Event ID was already seen in supplied evaluation context |
| `VERSION_CONFLICT` | Event's expected version differs from the current order version |
| `BLOCKED_INVALID_TRANSITION` | Requested state transition is not allowed |

## Exception triage policy

- **P1:** explicit financial risk, 3+ occurrences, or customer impact with age of at least 24 hours.
- **P2:** otherwise, customer impact, age of at least 12 hours, or 2+ occurrences.
- **P3:** remaining valid exceptions with a supported category.
- **Unknown category or invalid payload:** route to manual review; do not infer an operational action.

Supported routes: payment delay → payments operations; inventory mismatch → inventory operations; shipment delay → fulfilment operations; address validation → customer operations. These are illustrative synthetic rules.

## Reconciliation policy

- Compare only snapshots with the same order ID; mismatched IDs stop the comparison and require review.
- Status, total, and currency mismatches are HIGH severity and require human review.
- Item-count mismatches are MEDIUM severity and are reported without automatically requiring review.
- Both snapshots remain unchanged. The severity policy is illustrative and does not establish the authority of either source.

## Workflow governance policy

- Read-only inspection and internal draft preparation may proceed within their scoped policy.
- Customer-facing communication, financial transactions, order mutations, inventory mutations, and external-system changes require human approval before any separate execution layer acts.
- Invalid payloads and unknown action types go to manual review.
- The demo does not implement approval capture, identity verification, durable audit storage, or execution enforcement in another service.

Run `python examples/governance_demo.py` to see the decisions. The Mermaid flow is in `docs/ai-workflow-governance-flow.mmd`.

## Design principle

Use deterministic code for policy enforcement. Use AI, where appropriate, to summarize evidence or suggest next steps — never as the authority that bypasses transition rules, risk thresholds, or human approval requirements.

## Audit Trail + Human Review demo

Run `python examples/audit_demo.py`. The demo models immutable audit values and separate review dispositions. It is in-memory only; it does not provide durable storage, tamper-proof guarantees, or order mutation.

All examples use synthetic data and document assumptions, autonomy boundaries, and failure cases.
