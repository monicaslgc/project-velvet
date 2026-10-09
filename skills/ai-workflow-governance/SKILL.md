# AI Workflow Governance

## Purpose
Evaluate a proposed agent action against explicit autonomy boundaries before any execution layer can act. This is a reusable skill specification paired with a deterministic Python reference implementation.

## Required inputs
- action_id: non-empty string identifying the proposal
- action_type: supported action class
- requested_by: non-empty string naming the requesting agent or actor
- description: non-empty description of the proposed action

## Decision policy
1. Validate all required fields. Invalid input must fail closed to MANUAL_REVIEW.
2. Unknown action types must fail closed to MANUAL_REVIEW. Do not guess permissions.
3. READ_ONLY and INTERNAL_DRAFT may be allowed within their stated scope.
4. CUSTOMER_COMMUNICATION, FINANCIAL_TRANSACTION, ORDER_MUTATION, INVENTORY_MUTATION, and EXTERNAL_SYSTEM_CHANGE require human approval. They must not be autonomously executed.
5. Return a structured outcome, whether execution is allowed, whether approval is required, and human-readable reasons.
6. Preserve the proposal and do not call external systems or perform the proposed action.

## Safety boundaries
- ALLOW means the proposal passes this demo's policy; it does not mean this evaluator performed the action.
- REQUIRE_APPROVAL means a separate, authenticated approval and execution mechanism would be needed.
- MANUAL_REVIEW is the safe outcome for malformed or unsupported input.
- This demo does not implement identity verification, approval capture, durable audit storage, permission enforcement in an execution service, or real system integrations.
- Policy classes and thresholds are illustrative and must be reviewed against real business, legal, security, and operational requirements before production use.

## Validation
Run pytest and python examples/governance_demo.py.
