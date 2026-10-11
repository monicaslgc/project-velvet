# Scenario catalog

The canonical data pack uses stable scenario IDs so demos, tests, and walkthroughs can refer to the same fictional business case.

## Building-block scenarios

| Scenario ID | Scenario | Expected learning point | Useful demos |
|---|---|---|---|
| `happy-path-confirmation` | A created order is confirmed at the expected version | Valid lifecycle transition | Lifecycle, audit |
| `stale-shipment-event` | An event uses an outdated expected version | Detect a version conflict; request review | Lifecycle, audit, replay |
| `invalid-created-to-shipped` | A created order jumps directly to shipped | Reject invalid transition | Lifecycle, audit, evaluation |
| `duplicate-carrier-event` | A previously seen event ID is submitted again | Detect duplicate within supplied context | Lifecycle, audit |
| `shipment-delay-aged-customer-impact` | A delayed shipment has customer impact and is 30 hours old | Route as elevated priority | Exception triage, orchestrator |
| `payment-financial-risk` | A payment exception is flagged as financial risk | Prioritize financial investigation; do not retry automatically | Exception triage, governance |
| `unknown-exception-category` | Source provides an unmapped exception category | Fail closed to manual review | Exception triage, orchestrator |
| `snapshots-match` | Two source snapshots agree on checked fields | Confirm comparison consistency, not source authority | Reconciliation, orchestrator |
| `status-disagreement` | Two snapshots report different lifecycle states | High-severity mismatch requires human review | Reconciliation, orchestrator |
| `total-and-count-disagreement` | Totals and item counts differ | Monetary discrepancy is high severity | Reconciliation, orchestrator |
| `read-only-inspection` | Agent proposes read-only inspection | In-scope autonomous proposal | Governance, evaluation, replay |
| `customer-message-review` | Agent proposes a customer-facing message | Human approval required; no message sent | Governance, evaluation, replay, orchestrator |
| `inventory-adjustment-review` | Agent proposes a stock adjustment | Human approval required; no inventory changed | Governance, evaluation, replay |
| `unknown-action-type` | Agent proposes an unsupported action | Fail closed to manual review | Governance, evaluation, replay |
| `policy-relaxation-regression` | Candidate policy removes approval from risky actions | Flag risky policy drift before release | Evaluation, policy impact, release gate |

## Linked workflow scenarios

| Scenario ID | Scenario | Expected learning point | Useful demos |
|---|---|---|---|
| `shipment-delay-customer-review` | Aged shipment exception, customer message proposal, and status mismatch are linked into one workflow | Aggregate triage, reconciliation, and approval requirements | Orchestration |
| `unknown-exception-and-action` | Unmapped exception and unsupported action are linked into one workflow | Block automated progression when inputs cannot be safely classified | Orchestration |
| `payment-risk-review` | Financial-risk exception is paired with a proposed refund | Require human review; never issue the refund | Orchestration |

## Flagship: colour-restock incident

One fictional professional-colour restock order (`ord-4201`, six lines, EUR 184.50) loses a line because a shade is short. The same incident is evaluated at every stage, then with four different agent proposals. See the [flagship walkthrough](../docs/FLAGSHIP_SCENARIO.md).

| Scenario ID | Stage | Expected learning point |
|---|---|---|
| `colour-restock-incident` | Order record | The shared order for the whole incident |
| `colour-restock-out-of-order-event` | Lifecycle | A warehouse "shipped" event arrives for an order that never reached processing; blocked, not applied |
| `colour-restock-inventory-mismatch` | Triage | Third repeat, 26 hours old, customer impact: P1 to inventory operations with human review |
| `colour-restock-line-dropped` | Reconciliation | Total differs by EUR 30.75 (HIGH) and item count by one (MEDIUM); neither source is assumed correct |
| `colour-restock-read-only-inspection` | Orchestration | A permitted read-only proposal still leaves the incident in human review |
| `colour-restock-customer-notice` | Orchestration | A partial-shipment notice needs approval; nothing is sent |
| `colour-restock-stock-correction` | Orchestration | A stock correction needs approval; no inventory is changed |
| `colour-restock-auto-substitution` | Orchestration | An unsupported "substitute the shade automatically" action is blocked, not guessed into a known category |

The matching proposal records use the same IDs with a `-proposal` suffix.

IDs and outcomes are synthetic examples governed by this repository's current deterministic policies. They are not validated business rules for any real company.
