# Practical case-use examples

These examples show how Project Velvet's backend logic could be applied to operational workflows. All names, orders, events, and decisions are synthetic. They are portfolio scenarios, not claims about any real company's systems.

## Case 1 — A shipment delay with a customer update proposal

**Situation:** A fictional order is flagged as delayed. The operations workflow has evidence of a shipment exception and proposes sending a customer update.

**Workflow:** Exception triage classifies the issue and priority; orchestration collects the result; governance evaluates the proposed `CUSTOMER_COMMUNICATION` action.

**Expected result:** The exception is routed for operational review and the customer message requires human approval. The workflow explains why; it does not send a message or change the order.

**What to inspect:** `python examples/show_shipment_review.py` and `python examples/run_operational_workflow.py`.

## Case 2 — Order status differs between two snapshots

**Situation:** An order snapshot says `SHIPPED`, while another says `PROCESSING`.

**Workflow:** Reconciliation compares the supplied status, totals, currency, and item count and records mismatches with evidence.

**Expected result:** The discrepancy is reported with an illustrative severity and may be routed to human review. The demo does not decide which system is authoritative and does not repair either source.

**What to inspect:** `python examples/run_shared_dataset.py` and the reconciliation tests.

## Case 3 — A proposed refund or order mutation

**Situation:** An agent proposes a synthetic refund or changing an order's status.

**Workflow:** The proposal contract checks the exact required fields; governance checks the action type against an explicit policy.

**Expected result:** A well-formed proposal can still be denied autonomous execution and marked as requiring approval. Schema validity is not permission. No refund is issued and no order is changed.

**What to inspect:** `python examples/evaluate_agent_proposals.py` and `python examples/run_operational_workflow.py`.

## Case 4 — A policy change weakens approval boundaries

**Situation:** A candidate policy adds customer communication and financial transactions to its autonomous allow-list.

**Workflow:** The executable regression example evaluates the same stable synthetic cases under the default policy and a separately configured candidate policy, then compares the actual decisions.

**Expected result:** Newly allowed side-effecting proposals are reported as high-risk. Run `python examples/evaluate_policy_regression.py` to inspect the report. Run `python examples/evaluate_policy_regression.py --fail-on-high-risk` to make the demo gate exit non-zero when high-risk changes are detected.

**Safety note:** `examples/policy-candidate.json` is intentionally unsafe training data. It exists to demonstrate detection, not to recommend these permissions. The script does not execute proposed actions or deploy the candidate.

## Case 5 — Malformed or unfamiliar agent output

**Situation:** An agent returns a missing identifier, an unexpected action type, or a payload with extra fields.

**Workflow:** The proposal contract validates the shape before governance evaluates permission.

**Expected result:** Malformed proposals fail closed; unknown action types require manual review. A well-formed payload is not automatically trusted.

**What to inspect:** `python examples/evaluate_agent_proposals.py` and the adversarial tests.

## How to explain the value

The value proposition is **controlled, explainable workflow automation**: deterministic checks handle repeatable policy decisions, structured evidence makes exceptions easier to review, and approval boundaries prevent a proposed action from being mistaken for an executed action. The examples demonstrate testable logic and review controls; they do not quantify business impact or prove production readiness.
