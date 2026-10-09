# Skill: Policy Change Impact Analysis

## Purpose
Compare two versioned sets of recorded decision snapshots before a deterministic workflow policy is changed or released. Surface changes that may widen autonomy, remove human approval, block previously allowed actions, or reduce regression coverage.

## Inputs
- A non-blank baseline policy version and candidate policy version.
- Baseline and candidate lists containing unique, non-blank case IDs and decision snapshots.
- Each snapshot must include `outcome`, `allowed_to_execute`, `approval_required`, `valid`, and `reasons`.

## Procedure
1. Validate versions, case IDs, decision objects, required fields, and permission field types.
2. Compare cases by stable case ID, not list order.
3. Flag denied-to-allowed transitions as `NEWLY_ALLOWED` / HIGH risk.
4. Flag removal of an approval requirement as `APPROVAL_RELAXED` / HIGH risk.
5. Flag cases removed from the candidate set as `CASE_REMOVED` / HIGH risk because regression coverage may have been lost.
6. Report newly blocked, approval-tightened, outcome, validity, and reason changes. Added cases are MEDIUM risk; reason-only and unchanged cases are LOW risk.
7. Require a human to inspect high-risk changes and verify the underlying policy and business intent before release.

## Output
A deterministic report with baseline/candidate version labels, a primary category per case, a risk label, and explanatory details. When multiple changes occur on one case, all detected details are retained while the primary category prioritizes safety-relevant changes.

## Boundaries
This demo compares supplied snapshots; it does not execute policy code, independently establish whether snapshots are truthful, infer business context, decide that a release is safe, or deploy a change. Risk labels are illustrative triage signals, not a substitute for domain-owner review. Use synthetic data only.
