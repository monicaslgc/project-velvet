import json
from pathlib import Path

from velvet.release_readiness import build_release_readiness_report

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def build_report():
    return build_release_readiness_report(
        load_json("examples/agent-evaluation-cases.json"),
        load_json("contracts/ai-workflow-governance.json"),
        load_json("examples/decision-records.json"),
        load_json("examples/policy-version-comparison.json"),
    )


def test_integrated_report_aggregates_all_four_checks():
    report = build_report()
    assert set(report.checks) == {"regression", "skill_contracts", "decision_replay", "policy_impact"}
    assert report.checks["regression"].status == "PASS"
    assert report.checks["skill_contracts"].status == "PASS"
    assert report.checks["decision_replay"].status == "PASS"
    assert report.checks["policy_impact"].status == "FAIL"
    assert report.status == "BLOCKED"
    assert report.ready_for_human_review is False


def test_regression_failure_blocks_release():
    cases = load_json("examples/agent-evaluation-cases.json")
    cases[0]["expected"]["outcome"] = "REQUIRE_APPROVAL"
    report = build_release_readiness_report(
        cases,
        load_json("contracts/ai-workflow-governance.json"),
        load_json("examples/decision-records.json"),
        load_json("examples/policy-version-comparison.json"),
    )
    assert report.checks["regression"].status == "FAIL"
    assert report.status == "BLOCKED"
    assert report.ready_for_human_review is False


def test_safe_identical_policy_snapshots_allow_human_review_not_release_approval():
    comparison = load_json("examples/policy-version-comparison.json")
    comparison["candidate"] = comparison["baseline"]
    report = build_release_readiness_report(
        load_json("examples/agent-evaluation-cases.json"),
        load_json("contracts/ai-workflow-governance.json"),
        load_json("examples/decision-records.json"),
        comparison,
    )
    assert report.status == "READY_FOR_HUMAN_REVIEW"
    assert report.ready_for_human_review is True


def test_replay_drift_blocks_release():
    records = load_json("examples/decision-records.json")
    records[0]["recorded_decision"]["outcome"] = "REQUIRE_APPROVAL"
    report = build_release_readiness_report(
        load_json("examples/agent-evaluation-cases.json"),
        load_json("contracts/ai-workflow-governance.json"),
        records,
        load_json("examples/policy-version-comparison.json"),
    )
    assert report.checks["decision_replay"].status == "FAIL"
    assert report.status == "BLOCKED"
    assert report.ready_for_human_review is False
