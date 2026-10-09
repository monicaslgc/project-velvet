import json
from pathlib import Path

import pytest

from velvet.decision_replay import replay_records

ROOT = Path(__file__).resolve().parents[1]


def load_records():
    return json.loads((ROOT / "examples/decision-records.json").read_text(encoding="utf-8"))


def test_baseline_records_replay_without_drift():
    results = replay_records(load_records())
    assert len(results) == 3
    assert all(not result.changed for result in results)


def test_changed_recorded_outcome_is_reported_as_drift():
    records = load_records()
    records[0]["recorded_decision"]["outcome"] = "REQUIRE_APPROVAL"
    result = replay_records(records)[0]
    assert result.changed is True
    assert "outcome" in result.changed_fields


def test_changed_reason_is_reported_as_drift():
    records = load_records()
    records[0]["recorded_decision"]["reasons"] = ["Old policy reason"]
    result = replay_records(records)[0]
    assert result.changed is True
    assert "reasons" in result.changed_fields


def test_duplicate_record_ids_are_rejected():
    records = load_records()
    records.append(dict(records[0]))
    with pytest.raises(ValueError, match="duplicate record_id"):
        replay_records(records)


def test_malformed_record_is_rejected():
    records = load_records()
    records[0]["input"] = []
    with pytest.raises(ValueError, match="requires input and recorded_decision"):
        replay_records(records)
