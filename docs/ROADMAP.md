# Roadmap

What would be improved next, in priority order, and the reason for the order. Each item is a decision to take with the people who run the operation, not only a coding task.

## Done so far

- Deterministic policies for lifecycle, triage, reconciliation, and governance, each failing closed on invalid or unknown input.
- Orchestration where the strictest result wins, verified across all 54 combinations of outcomes ([scenario matrix](../tests/test_orchestrator_scenario_matrix.py)).
- Regression, replay, policy-impact analysis, and a release-readiness gate that never reports "approved".
- Boundary-value and adversarial tests, a test for every validator rejection path, and a test that runs every example script.
- A flagship incident that shows one situation producing four different outcomes depending only on the agent's proposal ([walkthrough](FLAGSHIP_SCENARIO.md)).

## Next

1. **Agree the rules with the business.** Every threshold here (for example, "over 24 hours with customer impact is top priority") is a placeholder. Which actions may run alone, and who approves the rest, is the first real decision, because everything else depends on it.
2. **Add real approvals.** "Needs a person" only works if there is a named person and a durable record of what they decided and when. Today the project returns the requirement but has no approval capture, identity, or audit storage.
3. **Run alongside people, read-only.** Connect to real systems only to observe, and compare the system's suggestions with what people decided. The agreement rate shows whether the rules are right before anything depends on them.
4. **Add domain rules with the people who own them.** For example, which colour-shade substitutions are acceptable and who must agree. Today an automatic substitution is blocked as an unknown action; a real version would model it as a supported action that always needs approval, introduced through the policy-change process below.
5. **Widen trust slowly.** Let low-risk actions run on their own, one type at a time, only where the evidence from step 3 supports it, and keep the release gate in front of every change.

## How a new rule would be introduced

The [extension guide](EXTENDING_THE_DEMOS.md) describes the path. In short: write the decision contract, add normal, borderline, malformed, and high-risk cases, bump the [policy version](POLICY_VERSIONING.md), compare baseline and candidate behaviour with the impact report, and let the release gate report on the result. A passing gate means a person may review the change; it never means the change is approved.

## Deliberately out of scope

Live integrations, a user interface, model calls, and anything that would execute a business action. The project exists to show how to decide safely, so those belong to a separate, separately reviewed layer.
