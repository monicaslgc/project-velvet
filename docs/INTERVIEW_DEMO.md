# Project Velvet — Interview Demo

## The 3-minute story

**Business problem:** A delayed order can create several separate operational questions at once: which team should investigate, do the available records agree, and can an agent send a customer update? Solving each question in isolation can hide the combined risk.

**Design proposal:** Coordinate small, deterministic checks and return one explainable review report. An AI agent may eventually help summarize evidence or draft a response, but the policy boundary—not the agent's confidence—decides whether an action can proceed.

**Important scope:** This is a synthetic backend portfolio demonstration. It is not a live Wella/WellaOne or Shopify integration, it does not call an LLM, and it does not send messages or mutate orders. The beauty-commerce setting is illustrative and does not imply knowledge of any company's internal systems.

## Run the flagship scenario

From the repository root:

```bash
python -m pip install -e ".[dev]"
python examples/show_shipment_review.py
```

The scenario `shipment-delay-customer-review` uses linked synthetic evidence:

- Order `ord-4105` has a 30-hour shipment-delay exception with customer impact declared.
- Two snapshots disagree: `CONFIRMED` versus `SHIPPED`.
- A proposed `CUSTOMER_COMMUNICATION` action is included.
- Triage prioritizes the exception, reconciliation preserves the disagreement as evidence, governance requires approval, and orchestration aggregates the results.
- The report must show that no customer message was sent and no order was changed.

Then show how the project checks changes rather than relying on a happy-path demo:

```bash
python examples/evaluate_triage_skill.py
python examples/evaluate_agent_proposals.py
python examples/evaluate_policy_regression.py
python examples/release_readiness_report.py
pytest
```

The candidate policy in the policy-regression example is intentionally unsafe training data. Its high-risk findings are expected; it is not a recommended policy. The release-readiness example demonstrates review gating, not automatic release approval.

## How to present it to a Digital Project Manager / AI workflow interviewer

### 1. Start with requirements, not technology

A reasonable initial requirement set for this synthetic case is:

- **R1 — Triage:** classify supported exception categories and provide priority, owner, and reasons.
- **R2 — Evidence:** compare the supplied order snapshots and identify discrepancies without silently choosing a source of truth.
- **R3 — Governance:** require approval for customer-facing communication and other side-effecting actions.
- **R4 — Traceability:** connect policy expectations to stable test-case IDs and executable checks.
- **R5 — Safe change:** flag policy changes that newly allow risky actions and require human review before release.

These are portfolio requirements written for the demo, not requirements extracted from a real company's internal platform.

### 2. Describe acceptance criteria

| Requirement | Acceptance evidence |
|---|---|
| R1 | The known shipment-delay case is assigned to the expected operational queue and elevated when the declared risk thresholds are met. |
| R2 | The status mismatch is reported with expected and observed values; neither snapshot is changed. |
| R3 | The customer communication proposal has `approval_required=true` and `allowed_to_execute=false`. |
| R4 | Versioned cases map to executable tests; CI fails when a tested expectation regresses. |
| R5 | A candidate policy that relaxes approval is identified as high risk; a human release decision remains necessary. |

The acceptance checks demonstrate encoded behavior for these fixtures. They do not prove the requirements are complete or validated against a real business process.

### 3. Explain the trade-offs

- **Deterministic policy for critical boundaries:** easier to inspect and regression-test than allowing an LLM to make final authorization decisions.
- **Human review instead of guessed repairs:** slower than automatic correction, but avoids inventing source-of-truth rules when systems disagree.
- **Small modules plus orchestration:** each policy is independently testable while a coordinator can present the combined case.
- **Synthetic fixtures first:** safe and repeatable for a portfolio; real rollout would require discovery, data contracts, system ownership, integration, access controls, persistence, observability, and operational support.

### 4. Discuss business value without inventing results

This repository does **not** measure savings, resolution time, customer satisfaction, or automation rates. In a real discovery and pilot, I would establish a baseline and agree with operations and product stakeholders on measures such as:

- time from exception creation to correct queue assignment;
- median time to resolve an exception;
- proportion of escalations later judged unnecessary;
- rate of reconciliation mismatches and time to disposition;
- proportion of proposed actions correctly routed to approval;
- policy-regression detection rate and false-positive rate;
- customer-contact delay and customer-impact outcomes.

Define each metric with an owner, numerator/denominator, data source, measurement window, and guardrail. Compare against a pre-pilot baseline and avoid attributing changes to automation without a suitable evaluation design.

## Interview-ready summary

> I built a synthetic backend workflow portfolio around a realistic operational problem: a delayed order, conflicting status evidence, and a proposed customer update. Instead of treating an agent recommendation as permission to act, the workflow separates triage, reconciliation, governance, and orchestration. The same scenario is backed by executable regression tests and a policy-change review example. I can walk through the requirements, acceptance criteria, trade-offs, and what I would measure in a pilot. It is deliberately not presented as a live integration or as evidence of measured business savings.

## Questions worth inviting

- Which system is authoritative for each order field, and who owns that decision?
- Which actions may be automated, and which require approval?
- What counts as a P1 exception, and who approves those thresholds?
- What evidence must be retained for an operational decision?
- What baseline and guardrail metrics would justify expanding a pilot?
- Who owns policy changes, test updates, and the final release decision?

Those are discovery questions, not assumptions encoded as real company policy.
