# Agent Proposal Output Contract

## Purpose

Agents and LLMs can return malformed, incomplete, or unexpected structured outputs. Before a proposed action reaches any separate execution layer, a system should validate its shape and apply the deterministic policy that owns authorization.

Project Velvet's `evaluate_agent_proposal` is a model-independent example of that boundary. It does not call a model and does not execute an action.

## Contract

The proposal must be a JSON object with exactly these fields, each a non-empty string:

- `action_id`
- `action_type`
- `requested_by`
- `description`

Missing fields, blank/non-string values, non-object payloads, or extra fields fail closed to `MANUAL_REVIEW`. Extra fields are rejected rather than silently ignored, because they may represent unsupported semantics that the receiving system has not agreed to interpret.

## Schema validity is not authorization

The report separates `schema_valid` from the governance decision:

- A structurally valid `READ_ONLY` proposal can receive `ALLOW`.
- A structurally valid `CUSTOMER_COMMUNICATION` proposal still receives `REQUIRE_APPROVAL`.
- An unknown action type can be schema-valid but receives `MANUAL_REVIEW`.
- A malformed payload is schema-invalid and cannot be allowed to execute.

Even `ALLOW` is a policy decision only. This demo has no execution adapter, approval capture, authentication, or external integration.

## Run and test

```bash
python examples/evaluate_agent_proposals.py
pytest tests/test_agent_action_contract.py
```

The versioned synthetic cases exercise safe read-only output, approval-gated communication, unknown actions, missing fields, and unexpected fields. The tests also pass a non-object payload directly to the validator, since JSON fixtures alone do not cover every in-memory caller behavior. A separate [governance boundary consistency test](GOVERNANCE_BOUNDARY_CONSISTENCY.md) checks that this validator and the core policy agree across the shared versioned case set.

## Limits

This contract does not assess whether an LLM's natural-language reasoning is correct, whether its description is truthful, or whether the proposed business action is appropriate for the real world. It checks a declared data shape and then applies explicit policy rules. A production boundary would also need authentication/authorization, schema versioning, durable audit records, idempotency, and a separately secured execution layer.
