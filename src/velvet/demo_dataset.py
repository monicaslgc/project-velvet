"""Integrity checks for the shared synthetic cross-demo dataset."""
from __future__ import annotations

COLLECTIONS = ("orders", "lifecycle_events", "exceptions", "snapshot_pairs", "proposed_actions", "policy_change_scenarios")

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
            for key in ("event_id", "exception_id", "action_id", "order_id", "case_id"):
                value = item.get(key)
                if value is not None and (not isinstance(value, str) or not value.strip()):
                    errors.append(f"{collection}[{index}].{key} must be a non-empty string when supplied.")
            record_id = item.get("order_id") or item.get("event_id") or item.get("exception_id") or item.get("action_id")
            if record_id:
                ids.append(record_id)
        if len(ids) != len(set(ids)):
            errors.append(f"{collection} contains duplicate primary identifiers.")
    order_ids = {x.get("order_id") for x in data.get("orders", []) if isinstance(x, dict)} if isinstance(data.get("orders"), list) else set()
    for collection in ("lifecycle_events", "exceptions", "snapshot_pairs"):
        items = data.get(collection, [])
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            if isinstance(item, dict) and item.get("order_id") not in order_ids:
                errors.append(f"{collection}[{index}] references an unknown order_id.")
    return errors
