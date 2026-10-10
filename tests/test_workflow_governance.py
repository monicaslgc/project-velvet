from velvet.workflow_governance import (
    ActionType, GovernanceOutcome, ProposedAction, evaluate_action,
)

def action(action_type: str) -> ProposedAction:
    return ProposedAction("act-001", action_type, "demo-agent", "Synthetic test proposal")

def test_read_only_action_is_allowed_without_execution_side_effects():
    result = evaluate_action(action(ActionType.READ_ONLY.value))
    assert result.outcome == GovernanceOutcome.ALLOW
    assert result.allowed_to_execute is True
    assert result.approval_required is False

def test_internal_draft_is_allowed():
    result = evaluate_action(action(ActionType.INTERNAL_DRAFT.value))
    assert result.outcome == GovernanceOutcome.ALLOW
    assert result.approval_required is False

def test_customer_communication_requires_human_approval():
    result = evaluate_action(action(ActionType.CUSTOMER_COMMUNICATION.value))
    assert result.outcome == GovernanceOutcome.REQUIRE_APPROVAL
    assert result.allowed_to_execute is False
    assert result.approval_required is True

def test_all_side_effecting_action_types_require_approval():
    for action_type in (
        ActionType.FINANCIAL_TRANSACTION, ActionType.ORDER_MUTATION,
        ActionType.INVENTORY_MUTATION, ActionType.EXTERNAL_SYSTEM_CHANGE,
    ):
        result = evaluate_action(action(action_type.value))
        assert result.outcome == GovernanceOutcome.REQUIRE_APPROVAL
        assert result.allowed_to_execute is False
        assert result.approval_required is True

def test_unknown_action_type_fails_closed():
    result = evaluate_action(action("MAGIC_AUTONOMOUS_ACTION"))
    assert result.outcome == GovernanceOutcome.MANUAL_REVIEW
    assert result.allowed_to_execute is False
    assert result.approval_required is True

def test_none_action_fails_closed():
    result = evaluate_action(None)
    assert result.outcome == GovernanceOutcome.MANUAL_REVIEW
    assert result.allowed_to_execute is False
    assert result.approval_required is True
    assert result.valid is False

def test_malformed_payload_fails_closed():
    result = evaluate_action(ProposedAction("", "READ_ONLY", "agent", "inspect"))
    assert result.outcome == GovernanceOutcome.MANUAL_REVIEW
    assert result.allowed_to_execute is False
    assert result.approval_required is True
    assert result.valid is False

def test_decision_is_explanatory_and_input_is_not_mutated():
    proposal = action(ActionType.ORDER_MUTATION.value)
    original = proposal
    result = evaluate_action(proposal)
    assert proposal == original
    assert result.reasons
    assert "human" in " ".join(result.reasons).lower()

def test_each_required_action_field_rejects_non_string_values():
    for field in ("action_id", "action_type", "requested_by", "description"):
        values = {"action_id": "act-001", "action_type": "READ_ONLY", "requested_by": "agent", "description": "inspect"}
        values[field] = 123
        result = evaluate_action(ProposedAction(**values))
        assert result.valid is False, field
        assert result.outcome == GovernanceOutcome.MANUAL_REVIEW, field
        assert result.allowed_to_execute is False, field
        assert result.approval_required is True, field


def test_whitespace_padded_action_type_is_not_normalized_to_permission():
    result = evaluate_action(action(" READ_ONLY "))
    assert result.outcome == GovernanceOutcome.MANUAL_REVIEW
    assert result.allowed_to_execute is False
    assert result.approval_required is True


def test_unknown_action_type_with_case_or_whitespace_variants_fails_closed():
    for value in ("read_only", "READ_ONLY ", " READ_ONLY"):
        result = evaluate_action(action(value))
        assert result.outcome == GovernanceOutcome.MANUAL_REVIEW, value
        assert result.allowed_to_execute is False, value

