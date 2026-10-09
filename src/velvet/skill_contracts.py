"""Validate traceability between a skill's requirements and regression cases."""

from __future__ import annotations

from typing import Any


def validate_skill_contracts(contract_doc: dict[str, Any], cases_doc: list[dict[str, Any]]) -> list[str]:
    """Return contract issues; an empty list means the declared mapping is consistent."""
    issues: list[str] = []
    contracts = contract_doc.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        return ["contracts must be a non-empty list"]

    case_ids: list[str] = []
    for case in cases_doc:
        case_id = case.get("case_id") if isinstance(case, dict) else None
        if not isinstance(case_id, str) or not case_id.strip():
            issues.append("evaluation cases must have a non-empty case_id")
        else:
            case_ids.append(case_id)
    if len(case_ids) != len(set(case_ids)):
        issues.append("evaluation case IDs must be unique")
    known_case_ids = set(case_ids)

    contract_ids: list[str] = []
    for index, contract in enumerate(contracts):
        if not isinstance(contract, dict):
            issues.append(f"contract at index {index} must be an object")
            continue
        contract_id = contract.get("contract_id")
        requirement = contract.get("requirement")
        mapped_ids = contract.get("case_ids")
        if not isinstance(contract_id, str) or not contract_id.strip():
            issues.append(f"contract at index {index} must have a non-empty contract_id")
        else:
            contract_ids.append(contract_id)
        if not isinstance(requirement, str) or not requirement.strip():
            issues.append(f"contract {contract_id or index} must describe its requirement")
        if not isinstance(mapped_ids, list) or not mapped_ids:
            issues.append(f"contract {contract_id or index} must map to at least one case_id")
            continue
        if any(not isinstance(item, str) or not item.strip() for item in mapped_ids):
            issues.append(f"contract {contract_id or index} contains a blank case_id")
            continue
        if len(mapped_ids) != len(set(mapped_ids)):
            issues.append(f"contract {contract_id or index} contains duplicate case IDs")
        for mapped_id in mapped_ids:
            if mapped_id not in known_case_ids:
                issues.append(f"contract {contract_id or index} references unknown case_id: {mapped_id}")
    if len(contract_ids) != len(set(contract_ids)):
        issues.append("contract IDs must be unique")
    return issues
