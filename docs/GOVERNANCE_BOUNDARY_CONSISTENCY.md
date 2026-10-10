# Cross-boundary governance consistency

Project Velvet has two layers for a proposed action:

1. `evaluate_agent_proposal` validates the exact external payload shape.
2. `evaluate_action` applies the deterministic policy that owns the decision.

The proposal boundary must not create a different permission decision from the core policy. The parity test in `tests/test_governance_boundary_consistency.py` runs every versioned case in `examples/agent-evaluation-cases.json` through both layers and compares outcome, execution permission, approval requirement, and validity.

It also checks that permission-like extra fields such as `approval_granted` and `allowed_to_execute` are rejected as unsupported input and cannot override the policy result.

Run:

```bash
pytest tests/test_governance_boundary_consistency.py
python examples/evaluate_agent_policy.py
python examples/evaluate_agent_proposals.py
python examples/check_skill_contracts.py
python examples/release_readiness_report.py
```

## How the checks relate

- **Agent policy regression:** expected decisions still match the deterministic evaluator.
- **Proposal contract:** untrusted payloads have the exact required shape before policy evaluation.
- **Boundary consistency:** the proposal boundary and core policy agree on every versioned case.
- **Skill contract validation:** the governance requirements point to existing unique evaluation case IDs.
- **Release readiness:** aggregates regression, skill-contract, decision-replay, and policy-snapshot evidence.

The parity test is part of the normal pytest suite, so CI runs it with the other tests. The release-readiness report does not currently expose it as a separate named check; it relies on CI's test suite to validate this code-level invariant. A green report remains `READY_FOR_HUMAN_REVIEW`, never release approval.

All fixtures are synthetic. These checks validate the encoded contract and policy, not LLM reasoning quality, requirement completeness, external authorization enforcement, or production safety.
