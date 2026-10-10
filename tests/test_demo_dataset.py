import json
from pathlib import Path

from velvet.demo_dataset import validate_dataset
from velvet.shared_scenarios import evaluate_shared_pack


def load_pack():
    return json.loads(Path("datasets/operational-demo-pack.json").read_text(encoding="utf-8"))


def test_shared_dataset_is_valid_and_cross_referenced():
    assert validate_dataset(load_pack()) == []


def test_dataset_must_be_explicitly_synthetic():
    data = load_pack()
    data["synthetic_data_only"] = False
    assert any("synthetic_data_only" in error for error in validate_dataset(data))


def test_dataset_rejects_unknown_order_references():
    data = load_pack()
    data["exceptions"][0]["order_id"] = "ord-does-not-exist"
    assert any("unknown order_id" in error for error in validate_dataset(data))


def test_dataset_rejects_duplicate_identifiers_within_collection():
    data = load_pack()
    data["orders"].append(dict(data["orders"][0]))
    assert any("duplicate primary identifiers" in error for error in validate_dataset(data))


def test_dataset_rejects_broken_workflow_links():
    data = load_pack()
    data["workflow_scenarios"][0]["action_id"] = "act-missing"
    assert any("unknown action_id" in error for error in validate_dataset(data))


def test_shared_pack_runs_through_all_five_demo_policies():
    results = evaluate_shared_pack(load_pack())
    assert {row["demo"] for row in results} == {
        "lifecycle", "triage", "reconciliation", "governance", "orchestration"
    }
    assert len(results) == 21


def test_lifecycle_scenarios_reach_expected_decisions():
    results = {row["scenario_id"]: row["decision"] for row in evaluate_shared_pack(load_pack()) if row["demo"] == "lifecycle"}
    assert results["happy-path-confirmation"] == "ALLOWED"
    assert results["stale-shipment-event"] == "VERSION_CONFLICT"
    assert results["invalid-created-to-shipped"] == "BLOCKED_INVALID_TRANSITION"
    assert results["duplicate-carrier-event"] == "DUPLICATE_EVENT"


def test_unknown_records_fail_closed():
    results = evaluate_shared_pack(load_pack())
    assert "manual_review" in next(row for row in results if row["scenario_id"] == "unknown-exception-category")["detail"]
    assert next(row for row in results if row["scenario_id"] == "unknown-action-type")["decision"] == "MANUAL_REVIEW"


def test_orchestration_scenarios_produce_review_and_blocked_outcomes():
    results = {row["scenario_id"]: row["decision"] for row in evaluate_shared_pack(load_pack()) if row["demo"] == "orchestration"}
    assert results["shipment-delay-customer-review"] == "HUMAN_REVIEW_REQUIRED"
    assert results["unknown-exception-and-action"] == "BLOCKED"
    assert results["payment-risk-review"] == "HUMAN_REVIEW_REQUIRED"
