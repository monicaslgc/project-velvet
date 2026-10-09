# Agent Evaluation & Regression

## Purpose
Run a version-controlled set of policy cases against a deterministic evaluator and detect behavior drift when the implementation changes.

## Workflow
1. Keep representative, synthetic cases in a versioned JSON fixture.
2. Give every case a unique non-empty case ID, explicit input, and expected output fields.
3. Run the same evaluator against all cases.
4. Compare only fields explicitly declared as expected.
5. Report pass/fail per case, totals, pass rate, and a non-zero process exit code if any case fails.
6. Review and intentionally update expectations when policy changes; never change expected values merely to hide an unexplained regression.

## Quality boundaries
- Include normal, approval-required, unknown-action, and malformed-input cases.
- Use synthetic or appropriately sanitized fixtures; do not commit customer or production data.
- A passing regression suite shows conformance to these encoded examples only. It does not prove policy completeness, security, fairness, or general LLM reasoning quality.
- This reference kit evaluates the deterministic workflow-governance policy. It does not call or benchmark a language model.
- Keep human approval and execution enforcement outside this test harness.

## Run
Run: python examples/evaluate_agent_policy.py
Run: pytest
