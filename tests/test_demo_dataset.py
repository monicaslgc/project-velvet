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


def test_shared_pack_runs_through_all_four_demo_policies():
    results = evaluate_shared_pack(load_pack())
    assert {row["demo"] for row in results} == {
        "lifecycle", "triage", "reconciliation", "governance"
    }
    assert len(results) == 18


def test_lifecycle_scenarios_reach_expected_decisions():
    results = {row["scenario_id"]: row["decision"] for row in evaluate_shared_pack(load_pack()) if row["demo"] == "lifecycle"}
    assert results["happy-path-confirmation"] == "ALLOWED"
    assert results["stale-shipment-event"] == "VERSION_CONFLICT"
    assert results["invalid-created-to-shipped"] == "BLOCKED_INVALID_TRANSITION"
    assert results["duplicate-carrier-event"] == "DUPLICATE_EVENT"


def test_unknown_records_fail_closed():
    results = evaluate_shared_pack(load_pack())
    assert next(row for row in results if row["scenario_id"] == "unknown-exception-category")["detail"].find("manual_review") >= 0
    assert next(row for row in results if row["scenario_id"] == "unknown-action-type")["decision"] == "MANUAL_REVIEW"
