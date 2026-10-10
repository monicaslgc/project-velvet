# Policy versioning and change control

## Current evaluator version

The deterministic workflow-governance evaluator is labelled `governance-v1` in `src/velvet/workflow_governance.py` as `POLICY_VERSION`.

Bump this identifier when a change alters a rule's behavior or the meaning of a decision. Documentation-only edits and tests that do not change behavior do not require a version bump. If a change is intended to preserve behavior, keep the version and prove that with regression tests.

## Safe policy-change workflow

1. **Describe the proposed change.** State the business reason, affected action types, intended behavior, and risks.
2. **Add or update regression cases.** Include normal, malformed, unknown, and adversarial inputs. Preserve cases that protect existing approval boundaries.
3. **Run the current evaluator.** Record its structured decisions and explanations for the same stable case IDs.
4. **Execute the same regression cases under both policy configurations.** Run `python examples/evaluate_policy_regression.py`. The runner evaluates the shared `agent-evaluation-cases.json` inputs under the default policy and the separately configured candidate in `examples/policy-candidate.json`, then compares the generated decision snapshots. Use `python examples/evaluate_policy_regression.py --fail-on-high-risk` to make high-risk findings return a non-zero exit code.
5. **Inspect the snapshot comparator separately if useful.** `python examples/analyze_policy_impact.py` uses a hand-authored fixture to demonstrate categories such as removed regression cases. It is not a live evaluator comparison.
6. **Inspect every high-risk change.** Newly allowed actions and removed approval requirements are classified HIGH by the demo's explicit heuristics. These labels are review signals, not a substitute for domain risk assessment.
7. **Run the release-readiness report.** Regression, contract, replay, and impact checks must be inspected together. A successful report only means the supplied checks permit human review.
8. **Require a human release decision.** No script in this repository approves or deploys policy.

## Implementation boundary

The executable regression example runs one deterministic evaluator twice using two explicit immutable policy configurations against the same synthetic cases. It generates both decision snapshots itself, so the reported differences come from actual evaluator outputs. The candidate configuration is intentionally unsafe training data, not a production recommendation. This is not two independently versioned code builds, and the script does not execute proposed business actions, approve a policy, or deploy anything.

The separate `policy-version-comparison.json` fixture remains hand-authored and is useful for exercising added/removed-case comparison logic; it is not a live evaluator comparison.

For a production implementation, persist versioned policy artifacts, tie each decision to the exact policy version and input evidence, generate candidate snapshots from isolated policy builds, and require authenticated review before deployment. Those capabilities are not implemented in this portfolio demo.

## Review checklist

- [ ] The policy change and its owner are documented.
- [ ] Stable regression case IDs are preserved or removed intentionally with explanation.
- [ ] Unknown and malformed inputs still fail closed.
- [ ] Customer communication and side-effecting actions still require approval unless a reviewed requirement explicitly changes that rule.
- [ ] Baseline/candidate differences and all HIGH-risk findings are explained.
- [ ] CI passes, and coverage/static-analysis results have been inspected.
- [ ] A human has reviewed and approved the change outside the demo's automated checks.
