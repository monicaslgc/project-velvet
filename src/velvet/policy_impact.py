"""Compare recorded policy snapshots and flag potentially risky changes.

This module compares supplied decision snapshots; it does not execute or evaluate
policy code and does not determine business risk beyond its explicit rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class PolicyChange:
    case_id: str
    category: str
    risk: str
    details: tuple[str, ...]


@dataclass(frozen=True)
class PolicyImpactReport:
    baseline_version: str
    candidate_version: str
    changes: tuple[PolicyChange, ...]

    @property
    def unchanged_count(self) -> int:
        return sum(change.category == "UNCHANGED" for change in self.changes)

    @property
    def high_risk_count(self) -> int:
        return sum(change.risk == "HIGH" for change in self.changes)


def _index_snapshot(rows: Iterable[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{label} snapshot at index {index} must be an object")
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"{label} snapshot at index {index} has a blank case_id")
        if case_id in indexed:
            raise ValueError(f"duplicate case_id in {label} snapshot: {case_id}")
        decision = row.get("decision")
        if not isinstance(decision, dict):
            raise ValueError(f"{label} snapshot {case_id} requires a decision object")
        required = ("outcome", "allowed_to_execute", "approval_required", "valid", "reasons")
        missing = [field for field in required if field not in decision]
        if missing:
            raise ValueError(f"{label} snapshot {case_id} missing decision fields: {', '.join(missing)}")
        if not isinstance(decision["allowed_to_execute"], bool) or not isinstance(decision["approval_required"], bool):
            raise ValueError(f"{label} snapshot {case_id} has non-boolean permission fields")
        if not isinstance(decision["reasons"], list):
            raise ValueError(f"{label} snapshot {case_id} reasons must be a list")
        indexed[case_id] = decision
    return indexed


def compare_policy_snapshots(
    baseline: Iterable[dict[str, Any]],
    candidate: Iterable[dict[str, Any]],
    baseline_version: str,
    candidate_version: str,
) -> PolicyImpactReport:
    """Compare two decision-snapshot sets and classify changes using explicit rules."""
    if not isinstance(baseline_version, str) or not baseline_version.strip():
        raise ValueError("baseline_version must be a non-blank string")
    if not isinstance(candidate_version, str) or not candidate_version.strip():
        raise ValueError("candidate_version must be a non-blank string")
    before = _index_snapshot(baseline, "baseline")
    after = _index_snapshot(candidate, "candidate")
    changes: list[PolicyChange] = []
    for case_id in sorted(set(before) | set(after)):
        if case_id not in before:
            changes.append(PolicyChange(case_id, "CASE_ADDED", "MEDIUM", ("Case exists only in candidate snapshot.",)))
            continue
        if case_id not in after:
            changes.append(PolicyChange(case_id, "CASE_REMOVED", "HIGH", ("Baseline case is absent from candidate snapshot; coverage may have been lost.",)))
            continue
        old, new = before[case_id], after[case_id]
        details: list[str] = []
        categories: list[str] = []
        high_risk = False
        if old["allowed_to_execute"] is False and new["allowed_to_execute"] is True:
            categories.append("NEWLY_ALLOWED")
            details.append("Execution permission changed from denied to allowed.")
            high_risk = True
        elif old["allowed_to_execute"] is True and new["allowed_to_execute"] is False:
            categories.append("NEWLY_BLOCKED")
            details.append("Execution permission changed from allowed to denied.")
        if old["approval_required"] is True and new["approval_required"] is False:
            categories.append("APPROVAL_RELAXED")
            details.append("Human-approval requirement was removed.")
            high_risk = True
        elif old["approval_required"] is False and new["approval_required"] is True:
            categories.append("APPROVAL_TIGHTENED")
            details.append("Human-approval requirement was added.")
        if old["outcome"] != new["outcome"]:
            categories.append("OUTCOME_CHANGED")
            details.append(f"Outcome changed from {old['outcome']} to {new['outcome']}.")
        if old["valid"] != new["valid"]:
            categories.append("VALIDITY_CHANGED")
            details.append(f"Validity changed from {old['valid']} to {new['valid']}.")
        if old["reasons"] != new["reasons"]:
            categories.append("REASONS_CHANGED")
            details.append("Decision explanation changed.")
        if not categories:
            categories.append("UNCHANGED")
            details.append("Compared decision fields are unchanged.")
        # The primary category is the most safety-relevant detected change.
        priority = ("NEWLY_ALLOWED", "APPROVAL_RELAXED", "CASE_REMOVED", "NEWLY_BLOCKED", "APPROVAL_TIGHTENED", "OUTCOME_CHANGED", "VALIDITY_CHANGED", "REASONS_CHANGED", "UNCHANGED")
        primary = next((item for item in priority if item in categories), categories[0])
        changes.append(PolicyChange(case_id, primary, "HIGH" if high_risk else ("LOW" if primary in ("UNCHANGED", "REASONS_CHANGED") else "MEDIUM"), tuple(details)))
    return PolicyImpactReport(baseline_version, candidate_version, tuple(changes))
