# Skill: Operational Workflow Orchestration

## Purpose
Coordinate deterministic exception triage, read-only order reconciliation, and action-governance checks into one explainable workflow report.

## Inputs
- A non-empty workflow identifier.
- A typed exception payload and a proposed action.
- Optional expected and observed order snapshots; supply both or neither.

## Procedure
1. Validate the workflow envelope and fail closed when required values are missing.
2. Classify and route the exception using the exception-triage policy.
3. Compare snapshots only when both are present; never assume a source is authoritative.
4. Evaluate the proposed action using the governance policy.
5. Aggregate findings using the strictest applicable status and preserve reasons.
6. Return a structured report. Never execute the proposed action or mutate an order.

## Status interpretation
- BLOCKED: invalid/unknown exception or action, invalid reconciliation data, or incomplete snapshot pair.
- HUMAN_REVIEW_REQUIRED: a high-priority exception, high-severity reconciliation mismatch, or action requiring approval.
- READY_FOR_HUMAN_REVIEW: checks found no blocker; this is not an execution approval.

## Safety boundaries
This skill uses synthetic inputs and deterministic local functions only. It does not connect to APIs, send customer messages, change orders, reserve inventory, issue refunds, or persist an audit trail. Policy thresholds are illustrative. A production orchestrator would need durable correlation and audit storage, authentication/authorization, retries, timeouts, privacy controls, and a separately enforced approval/execution boundary.
