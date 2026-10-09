# Skill: Order Lifecycle Consistency

## Purpose
Evaluate synthetic order events against deterministic lifecycle policy and return an explainable decision. This skill is a reusable instruction artifact for an agent; it is not a substitute for the policy engine.

## Inputs
- Event ID and order ID
- Claimed source status and target status
- Expected order version
- Authoritative current status and version
- Event IDs already seen in the evaluation context, if available

## Procedure
1. Validate required identifiers, status values, and non-negative integer versions.
2. Check for duplicate event ID before proposing any transition.
3. Compare expected version with the authoritative current version.
4. Confirm the event's source status matches the authoritative status.
5. Check the transition against the explicit allow-list.
6. Return a decision code, concise reason, and proposed status/version only when allowed.
7. Route invalid input and version conflicts for human review.

## Guardrails
- Never invent missing order facts or infer that an external action succeeded.
- Never bypass deterministic policy because a model believes a transition is likely.
- Never mutate an order, send a message, trigger payment, cancel, ship, or refund.
- Treat version conflicts as unresolved until the authoritative state is re-read and the event is evaluated again.
- Duplicate detection is only as strong as the event ledger supplied to the evaluator. Do not describe an in-memory check as production-grade idempotency.
- Keep customer, order, and business data synthetic in portfolio demonstrations.

## Output contract
Return one of: `ALLOWED`, `INVALID_INPUT`, `DUPLICATE_EVENT`, `VERSION_CONFLICT`, `BLOCKED_INVALID_TRANSITION`. Include a reason. Include proposed status/version only for `ALLOWED`. Set human review required for invalid input and version conflict.
