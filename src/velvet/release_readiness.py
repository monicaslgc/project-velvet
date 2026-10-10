"""Read-only release gate combining existing governance checks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from velvet.agent_evaluation import evaluate_cases
from velvet.decision_replay import replay_records
from velvet.policy_impact import compare_policy_snapshots
from velvet.skill_contracts import validate_skill_contracts


@dataclass(frozen=True)
class CheckSummary:
    status: str
    summary: str
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReleaseReadinessReport:
    baseline_version: str
    candidate_version: str
    status: str
    checks: dict[str, CheckSummary]

    @property
    def ready_for_human_review(self) -> bool:
        """Return whether encoded checks pass and a person may review the candidate.

        This does not approve, deploy, or authorize release of the candidate.
        """
        return self.status == "READY_FOR_HUMAN_REVIEW"


def build_release_readiness_report(
    cases: list[dict[str, Any]],
    contract_doc: dict[str, Any],
    records: list[dict[str, Any]],
    policy_comparison: dict[str, Any],
) -> ReleaseReadinessReport:
    """Aggregate regression, contract, replay and snapshot-comparison checks.

    The function never executes proposed business actions or deploys policy. Its
    status is a conservative review gate over the supplied synthetic evidence.
    """
    baseline_version = policy_comparison.get("baseline_version", "")
    candidate_version = policy_comparison.get("candidate_version", "")
    if not isinstance(baseline_version, str) or not baseline_version.strip():
        raise ValueError("policy comparison requires baseline_version")
    if not isinstance(candidate_version, str) or not candidate_version.strip():
        raise ValueError("policy comparison requires candidate_version")
    baseline = policy_comparison.get("baseline")
    candidate = policy_comparison.get("candidate")
    if not isinstance(baseline, list) or not isinstance(candidate, list):
        raise ValueError("policy comparison requires baseline and candidate lists")

    evaluation = evaluate_cases(cases)
    evaluation_status = "PASS" if evaluation.failed == 0 and evaluation.total > 0 else "FAIL"
    evaluation_details = tuple(
        f"{result.case_id}: {result.message}" for result in evaluation.results if not result.passed
    )
    checks: dict[str, CheckSummary] = {
        "regression": CheckSummary(
            evaluation_status,
            f"{evaluation.passed}/{evaluation.total} regression cases passed ({evaluation.pass_rate:.0%}).",
            evaluation_details,
        )
    }

    contract_issues = validate_skill_contracts(contract_doc, cases)
    checks["skill_contracts"] = CheckSummary(
        "PASS" if not contract_issues else "FAIL",
        f"{len(contract_doc.get('contracts', [])) if isinstance(contract_doc.get('contracts'), list) else 0} requirement contracts checked; {len(contract_issues)} issue(s).",
        tuple(contract_issues),
    )

    replay_results = replay_records(records)
    drift = [result for result in replay_results if result.changed]
    checks["decision_replay"] = CheckSummary(
        "PASS" if not drift and replay_results else "FAIL",
        f"{len(replay_results)} recorded decisions replayed; {len(drift)} drifted.",
        tuple(f"{result.record_id} ({result.case_id}): {', '.join(result.changed_fields)}" for result in drift),
    )

    impact = compare_policy_snapshots(baseline, candidate, baseline_version, candidate_version)
    high = [item for item in impact.changes if item.risk == "HIGH"]
    medium = [item for item in impact.changes if item.risk == "MEDIUM"]
    impact_status = "FAIL" if high else ("REVIEW" if medium else "PASS")
    impact_details = tuple(
        f"[{item.risk}] {item.case_id}: {item.category} — {' '.join(item.details)}"
        for item in impact.changes if item.risk != "LOW"
    )
    checks["policy_impact"] = CheckSummary(
        impact_status,
        f"{len(impact.changes)} cases compared; {len(high)} high-risk and {len(medium)} medium-risk change(s); {impact.unchanged_count} unchanged.",
        impact_details,
    )

    hard_failures = [name for name, check in checks.items() if check.status == "FAIL"]
    review_items = [name for name, check in checks.items() if check.status == "REVIEW"]
    if hard_failures:
        status = "BLOCKED"
    elif review_items:
        status = "REVIEW_REQUIRED"
    else:
        status = "READY_FOR_HUMAN_REVIEW"
    return ReleaseReadinessReport(baseline_version, candidate_version, status, checks)
