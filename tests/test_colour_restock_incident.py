"""Flagship incident: every stage and every proposal outcome is pinned to its dataset records."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

from velvet.demo_dataset import validate_dataset
from velvet.shared_scenarios import evaluate_shared_pack

ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "datasets" / "operational-demo-pack.json"


def load_pack():
    return json.loads(PACK_PATH.read_text(encoding="utf-8"))


def load_example_module():
    spec = importlib.util.spec_from_file_location(
        "show_colour_restock_incident", ROOT / "examples" / "show_colour_restock_incident.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def trace():
    return load_example_module().build_incident(load_pack())


def test_incident_records_are_valid_and_linked():
    assert validate_dataset(load_pack()) == []


def test_stage_1_out_of_order_carrier_event_is_blocked(trace):
    stage = trace["stage_1_lifecycle"]
    assert stage["decision"] == "BLOCKED_INVALID_TRANSITION"
    assert stage["order_currently"] == "CONFIRMED"
    assert "PROCESSING" in stage["reason"] and "CONFIRMED" in stage["reason"]


def test_stage_2_repeated_aged_mismatch_with_customer_impact_is_p1(trace):
    stage = trace["stage_2_triage"]
    assert (stage["priority"], stage["assigned_team"]) == ("P1", "inventory_operations")
    assert stage["human_review_required"] is True
    assert any("3 times" in r for r in stage["reasons"])
    assert any("24-hour threshold" in r for r in stage["reasons"])


def test_stage_3_dropped_line_is_a_high_severity_money_discrepancy(trace):
    stage = trace["stage_3_reconciliation"]
    assert stage["matched"] is False and stage["human_review_required"] is True
    assert [(d["field"], d["severity"]) for d in stage["discrepancies"]] == [
        ("total_minor_units", "HIGH"), ("item_count", "MEDIUM")]
    assert stage["discrepancies"][0]["expected"] - stage["discrepancies"][0]["observed"] == 3075
    assert stage["source_data_changed"] is False


EXPECTED = {
    "wf-8201": ("READ_ONLY", "ALLOW", True, False, "HUMAN_REVIEW_REQUIRED"),
    "wf-8202": ("CUSTOMER_COMMUNICATION", "REQUIRE_APPROVAL", False, True, "HUMAN_REVIEW_REQUIRED"),
    "wf-8203": ("INVENTORY_MUTATION", "REQUIRE_APPROVAL", False, True, "HUMAN_REVIEW_REQUIRED"),
    "wf-8204": ("AUTO_SUBSTITUTE_SHADE", "MANUAL_REVIEW", False, True, "BLOCKED"),
}


@pytest.mark.parametrize("workflow_id", EXPECTED)
def test_stage_4_each_proposal_reaches_its_expected_outcome(trace, workflow_id):
    action_type, outcome, allowed, approval, status = EXPECTED[workflow_id]
    item = next(w for w in trace["stage_4_proposals"] if w["workflow_id"] == workflow_id)
    assert item["proposed_action"]["type"] == action_type
    assert item["governance"] == {
        "outcome": outcome, "allowed_to_execute": allowed, "approval_required": approval}
    assert item["workflow_status"] == status
    assert item["action_executed"] is False


def test_even_a_read_only_proposal_does_not_make_the_incident_ready(trace):
    read_only = next(w for w in trace["stage_4_proposals"] if w["workflow_id"] == "wf-8201")
    assert read_only["governance"]["allowed_to_execute"] is True
    assert read_only["workflow_status"] != "READY_FOR_HUMAN_REVIEW"


def test_unsupported_substitution_is_blocked_not_guessed_into_a_known_category(trace):
    item = next(w for w in trace["stage_4_proposals"] if w["workflow_id"] == "wf-8204")
    assert item["workflow_status"] == "BLOCKED"
    assert any("could not safely classify" in r for r in item["reasons"])


def test_incident_script_and_shared_runner_agree():
    rows = {r["record_id"]: r["decision"] for r in evaluate_shared_pack(load_pack()) if r["demo"] == "orchestration"}
    assert {k: rows[k] for k in EXPECTED} == {k: v[4] for k, v in EXPECTED.items()}


def test_building_the_trace_does_not_modify_the_pack():
    pack = load_pack()
    before = copy.deepcopy(pack)
    load_example_module().build_incident(pack)
    assert pack == before


def test_incident_data_is_flagged_synthetic():
    assert load_pack()["synthetic_data_only"] is True
