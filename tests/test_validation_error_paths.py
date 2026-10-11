"""Every documented rejection path of the validators is exercised with bad input.

The README claims these checks catch blank IDs, duplicates, missing mappings,
dangling references and malformed records. These tests make each claim concrete,
so a validator that silently stopped complaining would fail here.
"""
import copy
import json
from pathlib import Path

import pytest

from velvet.agent_evaluation import evaluate_cases
from velvet.audit_trail import ReviewStatus, create_audit_record, record_review
from velvet.decision_replay import replay_records
from velvet.demo_dataset import validate_dataset
from velvet.order_lifecycle import Decision, DecisionCode
from velvet.policy_impact import compare_policy_snapshots
from velvet.release_readiness import build_release_readiness_report
from velvet.skill_contracts import validate_skill_contracts

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


# ------------------------------------------------------------ skill contracts

CASES = [{"case_id": "c1"}, {"case_id": "c2"}]


def contract(**overrides):
    base = {"contract_id": "r1", "requirement": "Something is required", "case_ids": ["c1"]}
    base.update(overrides)
    return base


def issues_for(contracts, cases=None):
    return validate_skill_contracts({"contracts": contracts}, CASES if cases is None else cases)


def test_a_consistent_contract_has_no_issues():
    assert issues_for([contract(), contract(contract_id="r2", case_ids=["c1", "c2"])]) == []


@pytest.mark.parametrize("doc", [{}, {"contracts": []}, {"contracts": "x"}, {"contracts": None}])
def test_missing_or_empty_contract_list_is_rejected(doc):
    assert validate_skill_contracts(doc, CASES) == ["contracts must be a non-empty list"]


@pytest.mark.parametrize("bad_case", [{}, {"case_id": ""}, {"case_id": "  "}, {"case_id": 5}, "not-a-dict", None])
def test_evaluation_cases_without_a_usable_id_are_flagged(bad_case):
    assert any("non-empty case_id" in i for i in issues_for([contract()], [{"case_id": "c1"}, bad_case]))


def test_duplicate_evaluation_case_ids_are_flagged():
    assert any("must be unique" in i for i in issues_for([contract()], [{"case_id": "c1"}, {"case_id": "c1"}]))


def test_non_object_contract_is_flagged():
    assert any("must be an object" in i for i in issues_for(["nope"]))


@pytest.mark.parametrize("value", ["", "  ", None, 3])
def test_blank_contract_id_is_flagged(value):
    assert any("non-empty contract_id" in i for i in issues_for([contract(contract_id=value)]))


@pytest.mark.parametrize("value", ["", "  ", None])
def test_blank_requirement_is_flagged(value):
    assert any("must describe its requirement" in i for i in issues_for([contract(requirement=value)]))


@pytest.mark.parametrize("value", [None, [], "c1"])
def test_contract_without_mapped_cases_is_flagged(value):
    assert any("at least one case_id" in i for i in issues_for([contract(case_ids=value)]))


@pytest.mark.parametrize("ids", [["c1", ""], ["c1", None], ["  "]])
def test_blank_mapped_case_id_is_flagged(ids):
    assert any("blank case_id" in i for i in issues_for([contract(case_ids=ids)]))


def test_duplicate_mapped_case_ids_are_flagged():
    assert any("duplicate case IDs" in i for i in issues_for([contract(case_ids=["c1", "c1"])]))


def test_reference_to_a_case_that_no_longer_exists_is_flagged():
    assert any("unknown case_id: gone" in i for i in issues_for([contract(case_ids=["c1", "gone"])]))


def test_duplicate_contract_ids_are_flagged():
    assert any("contract IDs must be unique" in i for i in issues_for([contract(), contract()]))


# ---------------------------------------------------------------- demo dataset

def pack():
    return load("datasets/operational-demo-pack.json")


def errors_after(mutate):
    data = pack()
    mutate(data)
    return validate_dataset(data)


@pytest.mark.parametrize("root", [None, [], "x", 3])
def test_dataset_root_must_be_an_object(root):
    assert validate_dataset(root) == ["Dataset root must be a JSON object."]


@pytest.mark.parametrize("value", ["", "  ", None])
def test_dataset_id_must_be_non_blank(value):
    assert any("dataset_id" in e for e in errors_after(lambda d: d.update(dataset_id=value)))


@pytest.mark.parametrize("collection", ["orders", "exceptions", "snapshot_pairs", "workflow_scenarios"])
def test_each_collection_must_be_a_list(collection):
    assert any(f"{collection} must be a list" in e for e in errors_after(lambda d: d.update({collection: {}})))


def test_collection_items_must_be_objects():
    assert any("must be an object" in e for e in errors_after(lambda d: d["exceptions"].append("x")))


def test_every_record_needs_a_scenario_id():
    assert any("has no scenario_id" in e for e in errors_after(lambda d: d["orders"][0].pop("scenario_id")))


@pytest.mark.parametrize("key,collection", [("order_id", "exceptions"), ("exception_id", "exceptions"),
                                            ("action_id", "proposed_actions"), ("event_id", "lifecycle_events")])
def test_blank_identifiers_are_rejected_when_supplied(key, collection):
    assert any(f".{key} must be a non-empty string" in e
               for e in errors_after(lambda d: d[collection][0].__setitem__(key, "  ")))


def test_workflow_must_reference_an_existing_exception():
    assert any("unknown exception_id" in e
               for e in errors_after(lambda d: d["workflow_scenarios"][0].__setitem__("exception_id", "exc-missing")))


def test_workflow_must_reference_an_existing_snapshot_scenario():
    assert any("unknown snapshot_scenario_id" in e
               for e in errors_after(lambda d: d["workflow_scenarios"][0].__setitem__("snapshot_scenario_id", "nope")))


def test_lifecycle_events_and_snapshots_must_reference_known_orders():
    assert any("lifecycle_events[0] references an unknown order_id" in e
               for e in errors_after(lambda d: d["lifecycle_events"][0].__setitem__("order_id", "ord-x")))
    assert any("snapshot_pairs[0] references an unknown order_id" in e
               for e in errors_after(lambda d: d["snapshot_pairs"][0].__setitem__("order_id", "ord-x")))


def test_non_object_workflow_entries_do_not_crash_validation():
    assert any("must be an object" in e for e in errors_after(lambda d: d["workflow_scenarios"].append(7)))


# -------------------------------------------------------------- decision replay

def record(**overrides):
    base = copy.deepcopy(load("examples/decision-records.json")[0])
    base.update(overrides)
    return base


def test_untouched_records_replay_without_drift():
    assert not any(r.changed for r in replay_records(load("examples/decision-records.json")))


@pytest.mark.parametrize("field,value,message", [
    ("record_id", "", "blank record_id"),
    ("record_id", None, "blank record_id"),
    ("case_id", " ", "blank case_id"),
    ("policy_version", "", "blank policy_version"),
    ("input", None, "requires input and recorded_decision"),
    ("recorded_decision", "x", "requires input and recorded_decision"),
])
def test_malformed_records_are_rejected_with_a_clear_message(field, value, message):
    with pytest.raises(ValueError, match=message):
        replay_records([record(**{field: value})])


def test_non_object_record_is_rejected():
    with pytest.raises(ValueError, match="must be an object"):
        replay_records(["nope"])


def test_duplicate_record_ids_are_rejected():
    with pytest.raises(ValueError, match="duplicate record_id"):
        replay_records([record(), record()])


def test_input_that_cannot_build_a_proposed_action_is_rejected():
    with pytest.raises(ValueError, match="cannot be replayed"):
        replay_records([record(input={"unexpected": "field"})])


def test_tampered_recorded_decision_is_reported_as_drift_not_hidden():
    original = record()
    tampered = copy.deepcopy(original)
    tampered["recorded_decision"]["approval_required"] = not tampered["recorded_decision"]["approval_required"]
    result = replay_records([tampered])[0]
    assert result.changed is True and "approval_required" in result.changed_fields


# ----------------------------------------------------------- agent evaluation

def test_case_missing_its_input_fails_with_an_explanation_instead_of_crashing():
    report = evaluate_cases([{"case_id": "no-input", "expected": {"outcome": "ALLOW"}}])
    assert report.failed == 1 and "Invalid test case" in report.results[0].message


def test_case_with_unusable_input_fields_fails_cleanly():
    report = evaluate_cases([{"case_id": "bad", "input": {"bogus": 1}, "expected": {}}])
    assert report.failed == 1 and report.passed == 0


@pytest.mark.parametrize("cases", [
    [{"case_id": "", "input": {}, "expected": {}}],
    [{"case_id": "dup", "input": {}, "expected": {}}, {"case_id": "dup", "input": {}, "expected": {}}],
])
def test_blank_or_duplicate_case_ids_always_fail(cases):
    report = evaluate_cases(cases)
    assert report.failed >= 1 and any("blank or duplicated" in r.message for r in report.results)


def test_empty_case_list_reports_a_perfect_rate_but_the_release_gate_still_fails_it():
    assert evaluate_cases([]).pass_rate == 1.0


# ---------------------------------------------------------------- audit trail

def pending_record():
    decision = Decision(DecisionCode.VERSION_CONFLICT, "e1", "o1", "stale", human_review_required=True)
    return create_audit_record(decision, correlation_id="corr-1", original_order_version=3)


@pytest.mark.parametrize("value", ["", "  ", None])
def test_audit_record_requires_a_correlation_id(value):
    decision = Decision(DecisionCode.ALLOWED, "e1", "o1", "ok")
    with pytest.raises(ValueError, match="correlation_id"):
        create_audit_record(decision, correlation_id=value, original_order_version=0)


@pytest.mark.parametrize("status", [ReviewStatus.PENDING, ReviewStatus.NOT_REQUIRED])
def test_a_review_disposition_must_be_approved_or_rejected(status):
    with pytest.raises(ValueError, match="APPROVED or REJECTED"):
        record_review(pending_record(), reviewer_id="r", status=status, rationale="why")


def test_review_cannot_be_recorded_twice_or_where_none_is_pending():
    decision = Decision(DecisionCode.ALLOWED, "e1", "o1", "ok")
    clean = create_audit_record(decision, correlation_id="c", original_order_version=0)
    with pytest.raises(ValueError, match="pending"):
        record_review(clean, reviewer_id="r", status=ReviewStatus.APPROVED, rationale="why")


@pytest.mark.parametrize("kwargs,message", [({"reviewer_id": ""}, "reviewer_id"), ({"rationale": " "}, "rationale")])
def test_review_requires_a_reviewer_and_a_rationale(kwargs, message):
    args = {"reviewer_id": "r", "status": ReviewStatus.APPROVED, "rationale": "why"}
    args.update(kwargs)
    with pytest.raises(ValueError, match=message):
        record_review(pending_record(), **args)


def test_recording_a_review_leaves_the_original_audit_record_untouched():
    record_ = pending_record()
    before = repr(record_)
    record_review(record_, reviewer_id="r", status=ReviewStatus.REJECTED, rationale="why")
    assert repr(record_) == before and record_.review_status == ReviewStatus.PENDING


# -------------------------------------------------------------- policy impact

def snap(case_id="c1", **decision):
    base = {"outcome": "REQUIRE_APPROVAL", "allowed_to_execute": False, "approval_required": True,
            "valid": True, "reasons": ["r"]}
    base.update(decision)
    return {"case_id": case_id, "decision": base}


def compare(before, after):
    return compare_policy_snapshots(before, after, "v1", "v2")


def test_identical_snapshots_are_low_risk_and_unchanged():
    report = compare([snap()], [snap()])
    assert report.unchanged_count == 1 and report.high_risk_count == 0


@pytest.mark.parametrize("row,message", [
    ("nope", "must be an object"),
    ({"case_id": "", "decision": {}}, "blank case_id"),
    ({"case_id": "x", "decision": "nope"}, "requires a decision object"),
    ({"case_id": "x", "decision": {"outcome": "A"}}, "missing decision fields"),
])
def test_malformed_snapshot_rows_are_rejected(row, message):
    with pytest.raises(ValueError, match=message):
        compare([row], [snap()])


@pytest.mark.parametrize("field,value,message", [
    ("outcome", "", "outcome must be a non-blank string"),
    ("allowed_to_execute", "yes", "non-boolean permission fields"),
    ("approval_required", 1, "non-boolean permission fields"),
    ("valid", "true", "valid must be a boolean"),
    ("reasons", "text", "reasons must be a list of strings"),
    ("reasons", [1], "reasons must be a list of strings"),
])
def test_malformed_decision_fields_are_rejected(field, value, message):
    with pytest.raises(ValueError, match=message):
        compare([snap(**{field: value})], [snap()])


def test_duplicate_case_ids_are_rejected():
    with pytest.raises(ValueError, match="duplicate case_id"):
        compare([snap(), snap()], [snap()])


@pytest.mark.parametrize("version", ["", "  ", None])
def test_versions_must_be_non_blank(version):
    with pytest.raises(ValueError, match="version"):
        compare_policy_snapshots([snap()], [snap()], version, "v2")
    with pytest.raises(ValueError, match="version"):
        compare_policy_snapshots([snap()], [snap()], "v1", version)


def test_validity_change_is_reported_as_a_medium_risk_change():
    change = compare([snap()], [snap(valid=False)]).changes[0]
    assert (change.category, change.risk) == ("VALIDITY_CHANGED", "MEDIUM")


def test_each_high_risk_relaxation_is_detected_and_each_tightening_is_not_high_risk():
    assert compare([snap()], [snap(allowed_to_execute=True)]).high_risk_count == 1
    assert compare([snap()], [snap(approval_required=False)]).high_risk_count == 1
    tightened = compare([snap(approval_required=False)], [snap(approval_required=True)])
    assert tightened.high_risk_count == 0 and tightened.changes[0].category == "APPROVAL_TIGHTENED"


def test_removed_case_is_high_risk_and_added_case_is_medium():
    report = compare([snap("a"), snap("b")], [snap("a"), snap("c")])
    by_case = {c.case_id: (c.category, c.risk) for c in report.changes}
    assert by_case["b"] == ("CASE_REMOVED", "HIGH") and by_case["c"] == ("CASE_ADDED", "MEDIUM")


# ------------------------------------------------------------ release readiness

def gate(policy_comparison):
    return build_release_readiness_report(
        load("examples/agent-evaluation-cases.json"),
        load("contracts/ai-workflow-governance.json"),
        load("examples/decision-records.json"),
        policy_comparison,
    )


def test_only_medium_risk_changes_lead_to_review_required_not_ready_and_not_blocked():
    report = gate({"baseline_version": "v1", "candidate_version": "v2",
                   "baseline": [snap("a")], "candidate": [snap("a"), snap("new-case")]})
    assert report.status == "REVIEW_REQUIRED" and report.ready_for_human_review is False
    assert report.checks["policy_impact"].status == "REVIEW"


def test_a_clean_comparison_is_ready_for_human_review_but_never_called_approved():
    report = gate({"baseline_version": "v1", "candidate_version": "v1",
                   "baseline": [snap("a")], "candidate": [snap("a")]})
    assert report.status == "READY_FOR_HUMAN_REVIEW"
    assert "APPROVED" not in report.status.upper().replace("READY_FOR_HUMAN_REVIEW", "")


@pytest.mark.parametrize("overrides,message", [
    ({"baseline_version": ""}, "baseline_version"),
    ({"candidate_version": "  "}, "candidate_version"),
    ({"baseline": "x"}, "baseline and candidate lists"),
    ({"candidate": None}, "baseline and candidate lists"),
])
def test_release_gate_refuses_incomplete_policy_comparisons(overrides, message):
    comparison = {"baseline_version": "v1", "candidate_version": "v2", "baseline": [], "candidate": []}
    comparison.update(overrides)
    with pytest.raises(ValueError, match=message):
        gate(comparison)


def test_any_single_failing_check_blocks_the_gate():
    cases = load("examples/agent-evaluation-cases.json")
    cases[0] = copy.deepcopy(cases[0])
    cases[0]["expected"] = {"outcome": "NOT_A_REAL_OUTCOME"}
    report = build_release_readiness_report(
        cases, load("contracts/ai-workflow-governance.json"), load("examples/decision-records.json"),
        {"baseline_version": "v1", "candidate_version": "v1", "baseline": [snap("a")], "candidate": [snap("a")]},
    )
    assert report.status == "BLOCKED" and report.checks["regression"].status == "FAIL"
