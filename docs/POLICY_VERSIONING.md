# Policy versioning and change control

## Current evaluator version

The deterministic workflow-governance evaluator is labelled `governance-v1` in `src/velvet/workflow_governance.py` as `POLICY_VERSION`.

Bump this identifier when a change alters a rule's behavior or the meaning of a decision. Documentation-only edits and tests that do not change behavior do not require a version bump. If a change is intended to preserve behavior, keep the version and prove that with regression tests.

## Safe policy-change workflow

1. **Describe the proposed change.** State the business reason, affected action types, intended behavior, and risks.
2. **Add or update regression cases.** Include normal, malformed, unknown, and adversarial inputs. Preserve cases that protect existing approval boundaries.
3. **Run the current evaluator.** Record its structured decisions and explanations for the same stable case IDs.
4. **Compare baseline and candidate snapshots.** Use `examples/policy-version-comparison.json` and `python examples/analyze_policy_impact.py` to inspect changes. The comparator highlights newly allowed actions, relaxed approval requirements, removed cases, and other differences.
5. **Inspect every high-risk change.** Newly allowed actions and removed approval requirements are classified HIGH by the demo's explicit heuristics. These labels are review signals, not a substitute for domain risk assessment.
6. **Run the release-readiness report.** Regression, contract, replay, and impact checks must be inspected together. A successful report only means the supplied checks permit human review.
7. **Require a human release decision.** No script in this repository approves or deploys policy.

## Important implementation boundary

The snapshot comparator compares the supplied baseline and candidate records; it does **not** execute two versions of the policy implementation. The bundled `policy-version-comparison.json` is a deliberately illustrative fixture designed to exercise the comparison logic. It should not be described as an automatically captured diff between two running implementations.

For a production implementation, persist versioned policy artifacts, tie each decision to the exact policy version and input evidence, generate candidate snapshots from isolated policy builds, and require authenticated review before deployment. Those capabilities are not implemented in this portfolio demo.

## Review checklist

- [ ] The policy change and its owner are documented.
- [ ] Stable regression case IDs are preserved or removed intentionally with explanation.
- [ ] Unknown and malformed inputs still fail closed.
- [ ] Customer communication and side-effecting actions still require approval unless a reviewed requirement explicitly changes that rule.
- [ ] Baseline/candidate differences and all HIGH-risk findings are explained.
- [ ] CI passes, and coverage/static-analysis results have been inspected.
- [ ] A human has reviewed and approved the change outside the demo's automated checks.
