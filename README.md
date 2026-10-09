# Project Velvet

**AI-ready operational workflows for professional beauty commerce — portfolio demonstrations.**

Project Velvet explores how backend workflows can make order operations more reliable, explainable, and safe to automate. It uses synthetic data and generic business scenarios. It is not a WellaOne implementation and is not affiliated with or connected to any real commerce platform.

## First demo: Order Lifecycle Consistency

A deterministic policy engine evaluates order events before any downstream system acts on them. It checks required fields, duplicate event IDs, expected order versions, and allowed state transitions.

### What this demonstrates
- Explicit business rules before AI-assisted recommendations
- Idempotency checks and optimistic-version conflict detection
- Fail-closed handling for invalid or conflicting input
- Structured, explainable decisions
- Reusable agent skill instructions
- Mermaid diagrams, synthetic fixtures, unit tests, and CI

### Scope boundaries
This demo is an in-memory evaluator. It does **not** persist an event ledger, mutate a real order, or trigger payment, cancellation, shipment, refund, or customer communication. Duplicate detection is only against IDs supplied in the current evaluation call; production-grade idempotency requires an atomic, durable event ledger. Version checking here detects conflicts but does not resolve concurrency by itself.

## Quick start
Requires Python 3.11+.
```bash
python -m pip install -e ".[dev]"
pytest
python examples/run_demo.py
python examples/audit_demo.py
```

## Repository map
```text
src/velvet/order_lifecycle.py
src/velvet/audit_trail.py
examples/orders.json
examples/run_demo.py
examples/audit_demo.py
docs/order-lifecycle-flow.mmd
docs/order-lifecycle-states.mmd
docs/audit-trail-review-flow.mmd
skills/order-lifecycle-consistency/SKILL.md
skills/audit-trail-human-review/SKILL.md
tests/test_order_lifecycle.py
tests/test_audit_trail.py
.github/workflows/tests.yml
```

## Decision outcomes
| Outcome | Meaning |
|---|---|
| `ALLOWED` | Event passes policy; proposed next state/version are returned |
| `INVALID_INPUT` | Required event data is missing or malformed |
| `DUPLICATE_EVENT` | Event ID was already seen in supplied evaluation context |
| `VERSION_CONFLICT` | Event's expected version differs from the current order version |
| `BLOCKED_INVALID_TRANSITION` | Requested state transition is not allowed |

## Design principle
Use deterministic code for policy enforcement. Use AI, where appropriate, to summarize evidence or suggest next steps — never as the authority that bypasses transition rules, version checks, or human approval requirements.

## Roadmap
1. Order Lifecycle Consistency
2. Order Exception Triage
3. Order Reconciliation
4. Audit Trail and Human Review
5. AI Workflow Governance
6. Regression scenarios and reusable skills

All examples use synthetic data and document assumptions, autonomy boundaries, and failure cases.

## Audit Trail + Human Review demo
Run `python examples/audit_demo.py`. The demo models immutable audit values and separate review dispositions. It is in-memory only; it does not provide durable storage, tamper-proof guarantees, or order mutation.
