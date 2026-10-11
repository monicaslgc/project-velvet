# Demo and policy reference

Detailed description of each demo and its policy. Everything here uses synthetic data; see the [README](../README.md) for the overview and quick start.

# Demos

## Demo 1: Order Lifecycle Consistency

A deterministic policy engine evaluates order events before any downstream system acts on them. It checks required fields, duplicate event IDs, expected order versions, and allowed state transitions.

## Demo 2: Order Exception Triage

A deterministic triage policy classifies synthetic exceptions, assigns a priority, routes each known category to a responsible operational team, explains the evidence behind the decision, and flags cases for human review. Unknown categories and malformed payloads fail closed to manual review. The [triage skill evaluation pack](../examples/triage-skill-evaluation-cases.json) tests routine routing, escalation thresholds, unknown categories, malformed values, and instruction-like free text; run `python examples/evaluate_triage_skill.py`. It checks conformance to encoded deterministic policy, not LLM reasoning quality.

## Demo 3: Order Reconciliation

A read-only comparison checks two snapshots of the same order across status, total, currency, and item count. It reports every mismatch with expected and observed values, applies an illustrative severity policy, and flags high-severity discrepancies for human review. It never assumes which source is authoritative and never repairs data automatically.

## Demo 4: AI Workflow Governance

A deterministic policy evaluates proposed agent actions against explicit autonomy boundaries. Read-only inspection and internal drafts are allowed within scope; customer communication, financial transactions, order or inventory mutations, and external system changes require human approval. Invalid or unknown actions fail closed to manual review. The evaluator only returns a decision; it never executes the action or integrates with external systems.

## Demo 5: Agent Evaluation & Regression Kit

A reusable regression harness runs versioned synthetic cases against the deterministic workflow-governance evaluator, compares declared expected fields, reports pass/fail and pass rate, and exits with code 1 if a regression is detected. It covers allowed actions, approval-required actions, unknown actions, and malformed input. This evaluates conformance to encoded policy cases; it does not benchmark an LLM or prove general reasoning quality.

## Agent proposal output contract

The strict [agent proposal contract](../src/velvet/agent_action_contract.py) validates untrusted proposed-action objects before applying the existing governance policy. It requires exactly four non-empty string fields, rejects missing or unexpected fields, and distinguishes schema validity from policy permission. Unknown action types are routed to manual review; side-effecting actions require approval. Run `python examples/evaluate_agent_proposals.py` to inspect synthetic passing and fail-closed cases.

This is a model-independent boundary for evaluating outputs from an agent adapter; it does not call an LLM, test model reasoning, or execute proposals. The cases and unit tests check that malformed output and policy violations cannot be mistaken for permission.

## Demo 6: Skill Contract Testing

A machine-readable contract links each in-scope AI workflow governance requirement to stable regression case IDs. A validator detects blank or duplicate contract IDs, missing mappings, duplicate evaluation IDs, and references to cases that no longer exist. Run `python examples/check_skill_contracts.py`. This checks mapping integrity only; it does not semantically prove that natural-language requirements are complete or fully tested. The initial contract covers the governance skill only.

## Demo 7: Decision Replay & Observability

A read-only replay tool compares synthetic historical decision snapshots with the current deterministic governance policy. It reports changed fields and policy-version context without overwriting the original record or executing actions. Run `python examples/replay_decisions.py`. The fixtures are synthetic; this is not a production logging, storage, privacy, or monitoring service.

## Demo 8: Policy Change Impact Analysis

A deterministic snapshot comparator matches baseline and candidate decision records by stable case ID, then highlights newly allowed actions, relaxed approval requirements, removed regression cases, newly blocked actions, and other changes. Run `python examples/analyze_policy_impact.py` to inspect the hand-authored comparator fixture. For an executable comparison, run `python examples/evaluate_policy_regression.py`: it evaluates the same regression cases under the default policy and an explicit candidate policy, then compares those actual decisions. The candidate is intentionally unsafe training data; `python examples/evaluate_policy_regression.py --fail-on-high-risk` demonstrates a non-zero gate result. Neither script executes actions or deploys policy.

## Demo 9: Release Readiness Gating

A read-only report aggregates four checks into one explainable gate: regression results, skill-contract traceability, historical decision replay, and baseline-versus-candidate policy impact. It reports per-check findings and returns a non-zero exit code unless the evidence reaches `READY_FOR_HUMAN_REVIEW`. The bundled candidate intentionally contains high-risk changes, so the example should be blocked. A passing report is not automatic release approval; human review remains mandatory. Run `python examples/release_readiness_report.py`.

## Demo 10: Operational Workflow Orchestration

A deterministic orchestrator coordinates exception triage, optional read-only order reconciliation, and proposed-action governance into one explainable report. It aggregates the strictest applicable outcome: blocked for invalid/unknown inputs, human review required for elevated risk or side-effecting proposals, and ready for human review when no blocker is found. The sample intentionally requires human review because customer communication is a gated action. It never executes an action or changes an order. Run `python examples/run_operational_workflow.py`.


## Shared demo data

The shared [synthetic operational demo pack](../datasets/operational-demo-pack.json) provides linked fictional orders, lifecycle events, exceptions, reconciliation snapshot pairs, proposed agent actions, and policy-change examples. Stable scenario IDs in [the scenario catalog](../datasets/SCENARIO_CATALOG.md) make it easier to reuse the same business case across several demos instead of inventing unrelated records for every module.

Run `python examples/run_shared_dataset.py` to validate the pack and evaluate lifecycle, triage, reconciliation, governance, linked end-to-end orchestration, and policy-change impact scenarios through the existing deterministic policy modules. The runner prints a scenario-by-scenario decision summary and performs no writes or external actions. Validate the pack alone with `python examples/validate_demo_dataset.py`; integrity and expected-outcome checks are also included in the test suite. The data is synthetic, uses EUR minor units for monetary examples, and intentionally includes normal, anomalous, risky, and unknown cases. Existing demos retain focused fixtures where that keeps their quick-start commands simple.

# Policies and gates

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

Supported routes: payment delay â†’ payments operations; inventory mismatch â†’ inventory operations; shipment delay â†’ fulfilment operations; address validation â†’ customer operations. These are illustrative synthetic rules.

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

Run `python examples/governance_demo.py` to see the decisions. The Mermaid flow is in `docs/diagrams/ai-workflow-governance-flow.mmd`.

## Agent evaluation and regression

Run `python examples/evaluate_agent_policy.py` to execute the versioned governance cases. Every case has a unique ID, explicit input, and expected output fields. A mismatch returns a failing process exit code so CI can detect policy drift. Update expected results only when a policy change is intentional and reviewed. The runner evaluates the deterministic policy implementation, not the general quality of an LLM.

## Skill contract traceability

The initial contract lives in `contracts/ai-workflow-governance.json` and maps the governance skill's four requirement groups to the versioned evaluation cases. Run `python examples/check_skill_contracts.py` to check references and IDs. A passing check confirms the mapping is structurally consistent, not that the requirements are complete or the tests are sufficient; review the skill and contract together when policy changes.

## Design principle

Use deterministic code for policy enforcement. Use AI, where appropriate, to summarize evidence or suggest next steps â€” never as the authority that bypasses transition rules, risk thresholds, or human approval requirements.

## Audit Trail + Human Review demo

Run `python examples/audit_demo.py`. The demo models immutable audit values and separate review dispositions. It is in-memory only; it does not provide durable storage, tamper-proof guarantees, or order mutation.

All examples use synthetic data and document assumptions, autonomy boundaries, and failure cases.

## Policy change impact analysis

Run `python examples/analyze_policy_impact.py` to compare the synthetic baseline and candidate snapshots. The report flags newly allowed actions and relaxed approval controls as HIGH risk, and removed regression cases as HIGH risk because test coverage may have been lost. Risk labels are explicit demo heuristics; a human must inspect the actual policy diff, confirm domain intent, and decide whether release is appropriate. The tool does not run or deploy policy code.

## Release readiness gate

Run `python examples/release_readiness_report.py` to combine regression evaluation, governance contract mapping, decision replay, and policy snapshot comparison. `BLOCKED` means a hard check failed or a HIGH-risk change was found; `REVIEW_REQUIRED` means medium-risk changes need inspection; `READY_FOR_HUMAN_REVIEW` means these encoded checks passed and no changes were classified above LOW risk. The last status is deliberately not called release-approved. The included candidate is intentionally unsafe and should return `BLOCKED` with a non-zero exit code. All inputs are synthetic, and the gate does not deploy policy or execute business actions.
