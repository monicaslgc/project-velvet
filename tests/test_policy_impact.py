import json
from pathlib import Path

import pytest

from velvet.policy_impact import compare_policy_snapshots

ROOT = Path(__file__).resolve().parents[1]


def load_fixture():
    return json.loads((ROOT / "examples/policy-version-comparison.json").read_text(encoding="utf-8"))


def test_fixture_flags_relaxed_controls_as_high_risk():
    data = load_fixture()
    report = compare_policy_snapshots(data["baseline"], data["candidate"], data["baseline_version"], data["candidate_version"])
    by_id = {item.case_id: item for item in report.changes}
    assert by_id["customer-message"].category == "NEWLY_ALLOWED"
    assert by_id["customer-message"].risk == "HIGH"
    assert by_id["financial-action"].category == "APPROVAL_RELAXED"
    assert by_id["read-only"].category == "UNCHANGED"
    assert report.high_risk_count == 2


def test_newly_blocked_and_approval_tightened_are_reported():
    before = [{"case_id": "x", "decision": {"outcome": "ALLOW", "allowed_to_execute": True, "approval_required": False, "valid": True, "reasons": []}}]
    after = [{"case_id": "x", "decision": {"outcome": "REQUIRE_APPROVAL", "allowed_to_execute": False, "approval_required": True, "valid": True, "reasons": []}}]
    report = compare_policy_snapshots(before, after, "v1", "v2")
    assert report.changes[0].category == "NEWLY_BLOCKED"
    assert "approval requirement was added" in " ".join(report.changes[0].details)
    assert report.changes[0].risk == "MEDIUM"


def test_added_and_removed_cases_are_detected():
    row = {"case_id": "x", "decision": {"outcome": "ALLOW", "allowed_to_execute": True, "approval_required": False, "valid": True, "reasons": []}}
    report = compare_policy_snapshots([row], [{**row, "case_id": "y"}], "v1", "v2")
    by_id = {item.case_id: item for item in report.changes}
    assert by_id["x"].category == "CASE_REMOVED"
    assert by_id["x"].risk == "HIGH"
    assert by_id["y"].category == "CASE_ADDED"


def test_reason_only_change_is_low_risk():
    before = [{"case_id": "x", "decision": {"outcome": "ALLOW", "allowed_to_execute": True, "approval_required": False, "valid": True, "reasons": ["old"]}}]
    after = [{"case_id": "x", "decision": {"outcome": "ALLOW", "allowed_to_execute": True, "approval_required": False, "valid": True, "reasons": ["new"]}}]
    result = compare_policy_snapshots(before, after, "v1", "v2").changes[0]
    assert result.category == "REASONS_CHANGED"
    assert result.risk == "LOW"


def test_duplicate_or_blank_case_ids_fail_closed():
    row = {"case_id": "x", "decision": {"outcome": "ALLOW", "allowed_to_execute": True, "approval_required": False, "valid": True, "reasons": []}}
    with pytest.raises(ValueError, match="duplicate case_id"):
        compare_policy_snapshots([row, row], [], "v1", "v2")
    with pytest.raises(ValueError, match="blank case_id"):
        compare_policy_snapshots([{**row, "case_id": " "}], [], "v1", "v2")


def test_missing_decision_fields_are_rejected():
    with pytest.raises(ValueError, match="missing decision fields"):
        compare_policy_snapshots([{"case_id": "x", "decision": {}}], [], "v1", "v2")
