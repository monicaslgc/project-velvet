# Scenario catalog

The canonical data pack uses stable scenario IDs so demos, tests, and walkthroughs can refer to the same fictional business case.

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

IDs and outcomes are synthetic examples governed by this repository's current deterministic policies. They are not validated business rules for any real company.
