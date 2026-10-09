"""Run the synthetic order lifecycle scenarios."""
import json
from pathlib import Path
from velvet.order_lifecycle import OrderEvent, OrderStatus, evaluate_event

source = Path(__file__).with_name("orders.json")
for scenario in json.loads(source.read_text(encoding="utf-8")):
    event = OrderEvent(event_id=scenario["event_id"], order_id=scenario["order_id"], from_status=OrderStatus(scenario["current_status"]), to_status=OrderStatus(scenario["to_status"]), expected_version=scenario["expected_version"])
    result = evaluate_event(event, current_status=OrderStatus(scenario["current_status"]), current_version=scenario["current_version"])
    print(f'{scenario["scenario"]}: {result.code} — {result.reason}')
