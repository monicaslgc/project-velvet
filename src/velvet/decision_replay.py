"""Structured, read-only decision records and replay comparison for synthetic demos."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from velvet.workflow_governance import ProposedAction, evaluate_action


@dataclass(frozen=True)
class DecisionRecord:
    record_id: str
    case_id: str
    policy_version: str
    input: dict[str, Any]
    recorded_decision: dict[str, Any]


@dataclass(frozen=True)
class ReplayResult:
    record_id: str
    case_id: str
    policy_version: str
    changed: bool
    recorded_decision: dict[str, Any]
    replayed_decision: dict[str, Any]
    changed_fields: tuple[str, ...]


def decision_snapshot(decision: Any) -> dict[str, Any]:
    """Return stable, JSON-friendly decision fields; exclude runtime-only details."""
    return {
        "outcome": decision.outcome.value,
        "allowed_to_execute": decision.allowed_to_execute,
        "approval_required": decision.approval_required,
        "valid": decision.valid,
        "reasons": list(decision.reasons),
    }


def replay_records(
    records: Iterable[dict[str, Any]],
    evaluator: Callable[[ProposedAction], Any] = evaluate_action,
) -> tuple[ReplayResult, ...]:
    """Re-evaluate recorded synthetic inputs and report decision drift without side effects."""
    results: list[ReplayResult] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(records):
        if not isinstance(raw, dict):
            raise ValueError(f"record at index {index} must be an object")
        record_id = raw.get("record_id")
        case_id = raw.get("case_id")
        policy_version = raw.get("policy_version")
        action_input = raw.get("input")
        recorded = raw.get("recorded_decision")
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError(f"record at index {index} has a blank record_id")
        if record_id in seen_ids:
            raise ValueError(f"duplicate record_id: {record_id}")
        seen_ids.add(record_id)
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"record {record_id} has a blank case_id")
        if not isinstance(policy_version, str) or not policy_version.strip():
            raise ValueError(f"record {record_id} has a blank policy_version")
        if not isinstance(action_input, dict) or not isinstance(recorded, dict):
            raise ValueError(f"record {record_id} requires input and recorded_decision objects")
        try:
            action = ProposedAction(**action_input)
            replayed = decision_snapshot(evaluator(action))
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError(f"record {record_id} cannot be replayed: {exc}") from exc
        keys = sorted(set(recorded) | set(replayed))
        changed_fields = tuple(key for key in keys if recorded.get(key) != replayed.get(key))
        results.append(ReplayResult(
            record_id=record_id,
            case_id=case_id,
            policy_version=policy_version,
            changed=bool(changed_fields),
            recorded_decision=recorded,
            replayed_decision=replayed,
            changed_fields=changed_fields,
        ))
    return tuple(results)
