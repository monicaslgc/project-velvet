# Skill: Release Readiness Gating

## Purpose
Aggregate deterministic evidence before a proposed workflow-policy release: regression conformance, governance skill-contract mapping, replay drift, and policy snapshot impact.

## Inputs
- Versioned regression cases with declared expected outcomes.
- Machine-readable skill contracts and the same regression case inventory.
- Structured synthetic decision records with historical decision snapshots.
- Baseline and candidate policy decision snapshots with version labels.

## Procedure
1. Run the regression evaluator and record pass/fail details.
2. Validate that each governance requirement maps to existing unique regression cases.
3. Replay recorded decision inputs against the current deterministic evaluator and identify changed fields.
4. Compare baseline and candidate policy snapshots by stable case ID.
5. Mark the report BLOCKED if regression cases fail, skill-contract mapping is invalid, replay fails or drifts, or high-risk policy changes are detected.
6. Mark REVIEW_REQUIRED if there are medium-risk policy changes but no hard failures.
7. Otherwise mark READY_FOR_HUMAN_REVIEW; this is not automatic release approval.
8. Preserve per-check summaries and actionable details so a reviewer can inspect evidence rather than rely only on a status label.

## Output
An aggregate report with policy version labels, per-check status, concise summaries, detailed findings, and an overall gate status. The command exits non-zero unless the report reaches READY_FOR_HUMAN_REVIEW.

## Safety boundaries
This is a local, read-only demonstration using synthetic files. It does not run a deployment, execute proposed business actions, approve a release, verify human identity, or prove natural-language requirements are complete. Snapshot comparison only compares the supplied evidence. Risk labels and gate rules are illustrative and must be reviewed by a domain owner before production use.
