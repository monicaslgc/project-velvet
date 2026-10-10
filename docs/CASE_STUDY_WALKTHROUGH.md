# Project Velvet: Case-study walkthrough

This guide presents the portfolio as a set of reviewable engineering case studies. Each case uses the same structure: problem, synthetic evidence, decision logic, expected result, verification, and limitations. For an interview-ready summary that also covers requirements, acceptance criteria, trade-offs, and proposed pilot metrics, see the [Interview Demo](INTERVIEW_DEMO.md).

All records are fictional. These examples demonstrate deterministic backend logic, not a live commerce platform, a deployed AI agent, or measured business outcomes.

## Quick start

Install the project and development dependencies, then run the examples from the repository root:

```bash
python -m pip install -e ".[dev]"
python examples/show_shipment_review.py
python examples/run_shared_dataset.py
python examples/evaluate_agent_proposals.py
python examples/evaluate_policy_regression.py
pytest
```

## Case 1 — A delayed shipment needs a customer update

**Problem**

A shipment has not advanced in the expected time window. Operations needs to prioritize the exception, check for conflicting order evidence, and decide whether a proposed customer update can proceed.

**Synthetic input evidence**

- Order: `ord-4105`
- Exception: `exc-6101`, category `SHIPMENT_DELAY`, aged 30 hours, customer impact declared
- Expected order status: `CONFIRMED`
- Observed fulfilment status: `SHIPPED`
- Proposed action: `act-7102`, type `CUSTOMER_COMMUNICATION`

These values come from `datasets/operational-demo-pack.json`.

**Decision logic**

1. Triage maps the known exception category and supplied context to a priority and responsible team.
2. Reconciliation reports the status disagreement without deciding which source is authoritative.
3. Governance classifies customer communication as requiring approval.
4. Orchestration combines the results into a review outcome.

**Expected result**

The linked scenario is routed for human review. The discrepancy is retained as evidence, the customer communication is not authorized for autonomous execution, and no order or external system is changed.

**Run and verify**

```bash
python examples/show_shipment_review.py
python examples/run_operational_workflow.py
pytest tests/test_exception_triage.py tests/test_order_reconciliation.py tests/test_workflow_governance.py tests/test_operational_orchestrator.py
```

**What this demonstrates:** composing small deterministic policies into one explainable operational report.

**Limitation:** priority thresholds and source records are illustrative; this does not connect to a carrier or send a message.

## Case 2 — Two systems disagree about an order

**Problem**

An order-management snapshot and a fulfilment snapshot report different values for the same order. Automatically overwriting either record would assume which source is correct.

**Synthetic input evidence**

The `status-disagreement` scenario for `ord-4105` compares `CONFIRMED` with `SHIPPED`. The `total-and-count-disagreement` scenario for `ord-4104` compares total minor units `8700` with `8900`, and item count `3` with `2`.

**Decision logic**

The reconciliation function compares the supplied fields and emits discrepancies, evidence and the demo's severity classification. It does not perform a repair or pick a source of truth.

**Expected result**

The report identifies the differing fields. The input snapshots remain unchanged and the issue is available for a human or downstream workflow to review.

**Run and verify**

```bash
python examples/run_shared_dataset.py
pytest tests/test_order_reconciliation.py tests/test_demo_dataset.py
```

**What this demonstrates:** data-quality checks that expose evidence instead of silently making an irreversible correction.

**Limitation:** the examples do not define authoritative-source precedence or resolve the mismatch.

## Case 3 — A proposed refund or order change

**Problem**

An agent proposes a financial transaction or a mutation. A structurally valid proposal must not be confused with permission to execute it.

**Synthetic input evidence**

The regression cases include `financial-action-needs-approval` and `order-mutation-needs-approval`. The shared pack also contains the `financial-refund-review` proposed action.

**Decision logic**

The proposal contract checks the exact four-field shape. Governance then checks the action type against explicit policy lists. Financial transactions and order mutations require human approval; malformed proposals fail closed and unknown action types go to manual review.

**Expected result**

The decision report can describe a valid proposal while still setting `allowed_to_execute=false` and `approval_required=true`. No refund is issued and no order is changed.

**Run and verify**

```bash
python examples/evaluate_agent_proposals.py
pytest tests/test_agent_action_contract.py tests/test_workflow_governance.py
```

**What this demonstrates:** separation of schema validation, authorization, and execution.

**Limitation:** no payment processor, order API, approval queue, or execution adapter exists in this portfolio.

## Case 4 — A policy change weakens a safety boundary

**Problem**

A candidate governance policy changes which action types may proceed autonomously. Reviewers need evidence of what changed before accepting that candidate.

**Synthetic input evidence**

`examples/policy-candidate.json` is deliberately unsafe training data: it adds `CUSTOMER_COMMUNICATION` and `FINANCIAL_TRANSACTION` to the autonomous allow-list. It must not be treated as a recommended policy.

**Decision logic**

The regression runner evaluates the same synthetic evaluation cases under the default and candidate policy configurations, creates decision snapshots from those actual evaluations, and compares them by stable case ID.

**Expected result**

Newly permitted side-effecting actions are reported as high-risk. With `--fail-on-high-risk`, the example returns a non-zero exit code when such findings exist.

**Run and verify**

```bash
python examples/evaluate_policy_regression.py
python examples/evaluate_policy_regression.py --fail-on-high-risk
pytest tests/test_policy_impact.py tests/test_workflow_governance.py
```

The first command is the report demonstration. The second command is intentionally expected to return exit code `1` for the unsafe candidate.

**What this demonstrates:** a repeatable, explainable regression check on actual evaluator outputs.

**Limitation:** this compares two policy configurations using the same evaluator, not two separately built software versions. It does not approve or deploy a policy.

## Case 5 — An agent returns malformed or unfamiliar output

**Problem**

An agent output omits a required field, contains an empty identifier, or proposes an action type that the policy does not recognize.

**Synthetic input evidence**

The regression suite includes `unknown-action-manual-review` and `blank-identifier-manual-review`. Adversarial unit tests cover malformed field types, empty strings, unexpected fields and attempts to bypass policy classification.

**Decision logic**

The contract rejects invalid proposal shapes. If a proposal is well-formed but the action type is unknown, governance still withholds autonomous execution and requests manual review.

**Expected result**

Invalid or unknown proposals never receive autonomous permission merely because they came from an agent.

**Run and verify**

```bash
python examples/evaluate_agent_proposals.py
pytest tests/test_agent_action_contract.py tests/test_workflow_governance.py
```

**What this demonstrates:** fail-closed handling at the boundary between untrusted agent output and deterministic workflow policy.

**Limitation:** this tests sample structured payloads; it does not call an LLM or measure model quality.

## Reviewer checklist

For each case, a reviewer should be able to answer:

- What exact synthetic input triggered the decision?
- Which deterministic rule or policy produced the outcome?
- What evidence and reason are returned?
- Which tests encode the expected behavior?
- What does the workflow deliberately refuse to do?
- What production capability would still need to be built and reviewed?

## Overall value proposition

Project Velvet demonstrates how operational automation can be made more reviewable by separating detection, prioritization, authorization, and execution. The code makes its decisions inspectable and testable, while the case studies make limitations explicit. It does not claim measured savings, production readiness, real integrations, or autonomous business execution.
