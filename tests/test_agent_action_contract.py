from velvet.agent_action_contract import evaluate_agent_proposal
from velvet.workflow_governance import GovernanceOutcome


def proposal(**overrides):
    result = {
        "action_id": "act-test-1",
        "action_type": "READ_ONLY",
        "requested_by": "demo-agent",
        "description": "Inspect synthetic order details.",
    }
    result.update(overrides)
    return result


def test_valid_read_only_proposal_passes_schema_and_policy():
    report = evaluate_agent_proposal(proposal())
    assert report.schema_valid is True
    assert report.issues == ()
    assert report.decision.outcome == GovernanceOutcome.ALLOW
    assert report.decision.allowed_to_execute is True


def test_side_effecting_proposal_is_valid_but_requires_approval():
    report = evaluate_agent_proposal(proposal(action_type="CUSTOMER_COMMUNICATION"))
    assert report.schema_valid is True
    assert report.decision.outcome == GovernanceOutcome.REQUIRE_APPROVAL
    assert report.decision.allowed_to_execute is False
    assert report.decision.approval_required is True


def test_unknown_action_type_is_schema_valid_but_sent_to_manual_review():
    report = evaluate_agent_proposal(proposal(action_type="UNRECOGNIZED_ACTION"))
    assert report.schema_valid is True
    assert report.decision.outcome == GovernanceOutcome.MANUAL_REVIEW
    assert report.decision.allowed_to_execute is False
    assert report.decision.approval_required is True


def test_missing_field_fails_closed():
    payload = proposal()
    del payload["description"]
    report = evaluate_agent_proposal(payload)
    assert report.schema_valid is False
    assert any("description" in issue for issue in report.issues)
    assert report.decision.outcome == GovernanceOutcome.MANUAL_REVIEW
    assert report.decision.allowed_to_execute is False
    assert report.decision.valid is False


def test_blank_field_fails_closed():
    report = evaluate_agent_proposal(proposal(requested_by="  "))
    assert report.schema_valid is False
    assert report.decision.outcome == GovernanceOutcome.MANUAL_REVIEW
    assert report.decision.allowed_to_execute is False


def test_extra_field_fails_closed_instead_of_being_silently_ignored():
    report = evaluate_agent_proposal(proposal(execute_immediately=True))
    assert report.schema_valid is False
    assert any("execute_immediately" in issue for issue in report.issues)
    assert report.decision.outcome == GovernanceOutcome.MANUAL_REVIEW
    assert report.decision.allowed_to_execute is False


def test_non_object_payload_fails_closed():
    report = evaluate_agent_proposal(["READ_ONLY", "inspect"])
    assert report.schema_valid is False
    assert report.decision.outcome == GovernanceOutcome.MANUAL_REVIEW
    assert report.decision.allowed_to_execute is False
