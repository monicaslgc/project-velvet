import json
from pathlib import Path

from velvet.agent_action_contract import evaluate_agent_proposal
from velvet.workflow_governance import ProposedAction, evaluate_action

ROOT = Path(__file__).resolve().parents[1]


def load_cases():
    return json.loads(
        (ROOT / "examples/agent-evaluation-cases.json").read_text(encoding="utf-8")
    )


def decision_fields(decision):
    return {
        "outcome": decision.outcome.value,
        "allowed_to_execute": decision.allowed_to_execute,
        "approval_required": decision.approval_required,
        "valid": decision.valid,
    }


def test_proposal_boundary_and_governance_evaluator_agree_on_every_versioned_case():
    for case in load_cases():
        payload = case["input"]
        boundary = evaluate_agent_proposal(payload)
        direct = evaluate_action(
            ProposedAction(
                action_id=payload["action_id"],
                action_type=payload["action_type"],
                requested_by=payload["requested_by"],
                description=payload["description"],
            )
        )
        expected = case["expected"]
        assert decision_fields(boundary.decision) == decision_fields(direct), case["case_id"]
        assert boundary.schema_valid is expected["valid"], case["case_id"]
        assert decision_fields(boundary.decision) == {
            key: expected[key] for key in decision_fields(boundary.decision)
        }, case["case_id"]


def test_extra_permission_like_fields_cannot_change_direct_policy_decision():
    base = {
        "action_id": "consistency-001",
        "action_type": "ORDER_MUTATION",
        "requested_by": "demo-agent",
        "description": "Change synthetic order status.",
    }
    baseline = evaluate_agent_proposal(base)
    forged = evaluate_agent_proposal(
        base | {"approval_granted": True, "allowed_to_execute": True}
    )
    assert baseline.decision.outcome.value == "REQUIRE_APPROVAL"
    assert forged.schema_valid is False
    assert forged.decision.allowed_to_execute is False
    assert forged.decision.approval_required is True
