# Project Velvet: Portfolio Walkthrough

This is a guided path for reviewers who want to understand the design decisions without reading every module first.

## Five-minute walkthrough

### 1. Start with a concrete operational risk

Use the shared scenario `stale-shipment-event`. The incoming event refers to an older expected order version. The lifecycle evaluator checks the event against the known transition and version rules rather than accepting it just because the event looks plausible.

**Talk about:** event ordering, duplicate detection, optimistic concurrency, and why a rejected event should carry an explanation.

### 2. Follow an exception into triage

Use `shipment-delay-aged-customer-impact`. Triage considers the category and declared context such as age and customer impact, then returns a priority and routing recommendation.

**Talk about:** explainable prioritization, queue ownership, thresholds as policy rather than magic, and the danger of silently routing an unknown category.

### 3. Compare evidence before deciding what to do

Use `status-disagreement` or `total-and-count-disagreement`. Reconciliation reports the fields that differ and applies the demo's severity policy.

**Talk about:** why comparing records is different from resolving the disagreement; why the system should not assume which source is authoritative; and why monetary discrepancies deserve careful handling.

### 4. Apply the autonomy boundary

Use `customer-message-review` or `inventory-adjustment-review`. Governance evaluates the proposed action and marks approval as required. Nothing is sent or changed.

**Talk about:** the difference between an AI-generated recommendation and permission to execute it; least privilege; explicit action types; and fail-closed defaults.

### 5. Inspect the agent output boundary

Run `python examples/evaluate_agent_proposals.py`. The proposal contract accepts only the declared four-field shape, rejects missing or unexpected fields, then applies the deterministic governance policy. Compare schema validity with the policy outcome: an unknown action can be structurally well-formed and still require manual review.

**Talk about:** structured outputs, strict schemas, separation of syntax from authorization, fail-closed behavior, and why validating an agent proposal is not the same as trusting or executing it.

### 6. Prove that the behavior remains reviewable

Run the agent evaluation, proposal contract checks, skill-contract validation, replay, policy impact comparison, and release-readiness example.

**Talk about:** how stable IDs connect requirements to tests; how a changed decision can be detected; and why “all tests pass” is not equivalent to “the policy is correct.”

## End-to-end orchestration story

The shared scenario `shipment-delay-customer-review` links an aged shipment exception, a customer-message proposal, and a status mismatch. The orchestrator can combine triage, governance, and optional reconciliation evidence into one structured report.

This is useful because a single business situation often crosses team boundaries. The point is not to collapse all policies into one giant rule; it is to keep each decision understandable and combine their results at a coordination layer.

Use `python examples/show_shipment_review.py` for a structured, end-to-end output from the linked shipment-delay fixture. It invokes the existing modules and checks that its orchestration status agrees with the shared runner. Use `python examples/run_shared_dataset.py` to inspect the full shared runner's outputs. Use `docs/operational-workflow-orchestration-flow.mmd` for the orchestration diagram.

## Discussion prompts for a technical review

1. **Why deterministic rules instead of an LLM making the final decision?** Critical transitions, permissions, and approval boundaries need explicit, testable behavior. An AI component may help summarize evidence or suggest next steps, but should not bypass policy.
2. **What does “fail closed” mean here?** Unknown or malformed input should not be interpreted as permission. The evaluator returns a blocked or human-review outcome according to its policy.
3. **How would you prevent duplicate processing in a real system?** This demo checks duplicate event IDs in the supplied context. A production implementation would also need a durable idempotency strategy, persistence, concurrency controls, and operational recovery.
4. **How would you tune prioritization?** Establish domain-owned definitions, inspect historical examples, validate thresholds with stakeholders, measure false positives and missed urgent cases, and version policy changes. The current rules are illustrative.
5. **How would you know whether a policy change is safe?** Compare baseline and candidate decisions, run regression cases, check requirement-to-test links, review newly allowed or less-protected actions, and require a human release decision.
6. **What are the limitations of the current audit demo?** It represents audit data and review dispositions in memory. Production auditability would require persistence, access controls, retention rules, integrity protections, and monitoring.
7. **What does the test suite prove?** It proves that tested cases match encoded expectations. It cannot prove that every scenario is covered or that the policy reflects every business requirement.

## Honest scope statement

Project Velvet is a backend workflow portfolio, not a production integration. It uses synthetic data and generic scenarios. It demonstrates explicit policy evaluation, structured reasons, conservative escalation, linked test evidence, and release checks. Real deployment would require domain validation, integrations, persistence, security review, observability, ownership, and operational support.
