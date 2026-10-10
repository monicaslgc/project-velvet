"""Integrity checks for the shared synthetic cross-demo dataset."""
from __future__ import annotations

COLLECTIONS = (
    "orders", "lifecycle_events", "exceptions", "snapshot_pairs",
    "proposed_actions", "policy_change_scenarios", "workflow_scenarios",
)


def validate_dataset(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Dataset root must be a JSON object."]
    if data.get("synthetic_data_only") is not True:
        errors.append("synthetic_data_only must be true.")
    if not isinstance(data.get("dataset_id"), str) or not data["dataset_id"].strip():
        errors.append("dataset_id must be a non-empty string.")

    for collection in COLLECTIONS:
        items = data.get(collection)
        if not isinstance(items, list):
            errors.append(f"{collection} must be a list.")
            continue
        ids = []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{collection}[{index}] must be an object.")
                continue
            scenario = item.get("scenario_id")
            if not isinstance(scenario, str) or not scenario.strip():
                errors.append(f"{collection}[{index}] has no scenario_id.")
            for key in (
                "event_id", "exception_id", "action_id", "order_id",
                "case_id", "workflow_id",
            ):
                value = item.get(key)
                if value is not None and (not isinstance(value, str) or not value.strip()):
                    errors.append(f"{collection}[{index}].{key} must be a non-empty string when supplied.")
            record_id = (
                item.get("workflow_id") or item.get("order_id") or item.get("event_id")
                or item.get("exception_id") or item.get("action_id")
            )
            if record_id:
                ids.append(record_id)
        if len(ids) != len(set(ids)):
            errors.append(f"{collection} contains duplicate primary identifiers.")

    order_ids = {
        x.get("order_id") for x in data.get("orders", []) if isinstance(x, dict)
    } if isinstance(data.get("orders"), list) else set()
    for collection in ("lifecycle_events", "exceptions", "snapshot_pairs"):
        items = data.get(collection, [])
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            if isinstance(item, dict) and item.get("order_id") not in order_ids:
                errors.append(f"{collection}[{index}] references an unknown order_id.")

    exception_ids = {
        x.get("exception_id") for x in data.get("exceptions", []) if isinstance(x, dict)
    } if isinstance(data.get("exceptions"), list) else set()
    action_ids = {
        x.get("action_id") for x in data.get("proposed_actions", []) if isinstance(x, dict)
    } if isinstance(data.get("proposed_actions"), list) else set()
    snapshot_scenarios = {
        x.get("scenario_id") for x in data.get("snapshot_pairs", []) if isinstance(x, dict)
    } if isinstance(data.get("snapshot_pairs"), list) else set()
    workflows = data.get("workflow_scenarios", [])
    if isinstance(workflows, list):
        for index, workflow in enumerate(workflows):
            if not isinstance(workflow, dict):
                continue
            if workflow.get("exception_id") not in exception_ids:
                errors.append(f"workflow_scenarios[{index}] references an unknown exception_id.")
            if workflow.get("action_id") not in action_ids:
                errors.append(f"workflow_scenarios[{index}] references an unknown action_id.")
            snapshot_ref = workflow.get("snapshot_scenario_id")
            if snapshot_ref is not None and snapshot_ref not in snapshot_scenarios:
                errors.append(f"workflow_scenarios[{index}] references an unknown snapshot_scenario_id.")
    return errors
