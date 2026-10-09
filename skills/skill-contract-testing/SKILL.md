# Skill Contract Testing

## Purpose
Maintain an explicit, reviewable link between a skill's stated requirements and executable regression cases. Use this check when a policy skill or its evaluation cases change.

## Procedure
1. Express each in-scope requirement as a stable, unique contract ID.
2. Map each requirement to one or more stable evaluation case IDs.
3. Run the contract checker to detect missing mappings, duplicate IDs, and references to missing cases.
4. Run the full test suite and the agent evaluation regression runner.
5. Review changes to both the policy and expected results; do not update expected outcomes solely to make a failing test pass.

## Safety and limitations
- A valid mapping proves only that declared IDs are traceable; it does not prove the cases fully test a requirement.
- The initial contract covers the AI workflow governance skill only.
- Natural-language skill documentation is not parsed or semantically verified by this demo. Human review is still needed to keep contract descriptions faithful to the skill.
- This checker does not execute agent actions or connect to external systems.

## Validation
Run `python examples/check_skill_contracts.py` and `pytest`.
