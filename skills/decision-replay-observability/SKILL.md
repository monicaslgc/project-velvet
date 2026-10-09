# Decision Replay & Observability

## Purpose
Compare a recorded decision snapshot with the result of evaluating the same synthetic input under the current deterministic policy. Use replay to identify policy drift and support review before a policy release.

## Record contract
Each record includes:
- a unique, non-empty record ID
- a stable case ID
- the policy version used for the recorded decision
- the original structured input
- the recorded outcome, execution permission, approval flag, validity and reasons

## Procedure
1. Keep a versioned, privacy-reviewed decision record.
2. Replay only records whose input is appropriate for the test environment.
3. Compare stable decision fields, including reasons, rather than comparing timestamps or unstable runtime metadata.
4. Investigate every changed outcome or safety-relevant field before adopting a policy change.
5. Keep the historical record immutable; replay reports differences and does not overwrite history.

## Safety and limitations
- This repository uses synthetic examples only.
- The demo is an in-memory/file-based comparison, not a production observability platform.
- It does not persist records, authenticate actors, redact sensitive fields, execute proposed actions, or integrate with external systems.
- A changed reason can be useful to review but is not necessarily a change in permission; inspect the changed fields and context.
- Matching records demonstrate consistency for these examples only, not correctness for all possible inputs.
- Real deployments need access controls, retention rules, data minimisation, privacy review, integrity controls and a defined policy-versioning scheme.

## Validation
Run python examples/replay_decisions.py and pytest.
