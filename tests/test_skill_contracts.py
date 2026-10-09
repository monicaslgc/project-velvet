import json
from pathlib import Path

from velvet.skill_contracts import validate_skill_contracts

ROOT = Path(__file__).resolve().parents[1]


def load_contracts():
    return json.loads((ROOT / "contracts/ai-workflow-governance.json").read_text())


def load_cases():
    return json.loads((ROOT / "examples/agent-evaluation-cases.json").read_text())


def test_governance_contracts_reference_existing_unique_cases():
    assert validate_skill_contracts(load_contracts(), load_cases()) == []


def test_missing_case_reference_is_reported():
    contracts = load_contracts()
    contracts["contracts"][0]["case_ids"].append("case-that-does-not-exist")
    assert any("unknown case_id" in issue for issue in validate_skill_contracts(contracts, load_cases()))


def test_requirement_without_case_mapping_is_reported():
    contracts = load_contracts()
    contracts["contracts"][0]["case_ids"] = []
    assert any("at least one case_id" in issue for issue in validate_skill_contracts(contracts, load_cases()))


def test_duplicate_contract_ids_are_reported():
    contracts = load_contracts()
    contracts["contracts"][1]["contract_id"] = contracts["contracts"][0]["contract_id"]
    assert any("contract IDs must be unique" in issue for issue in validate_skill_contracts(contracts, load_cases()))


def test_duplicate_evaluation_case_ids_are_reported():
    cases = load_cases()
    cases.append(dict(cases[0]))
    assert any("evaluation case IDs must be unique" in issue for issue in validate_skill_contracts(load_contracts(), cases))
