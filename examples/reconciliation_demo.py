"""Run read-only reconciliation over synthetic order snapshots."""
import json
from pathlib import Path
from velvet.order_reconciliation import OrderSnapshot, reconcile_orders

def main() -> None:
    records = json.loads(Path(__file__).with_name("reconciliation.json").read_text(encoding="utf-8"))
    for row in records:
        expected = OrderSnapshot(order_id=row["order_id"], **row["expected"])
        observed = OrderSnapshot(order_id=row["order_id"], **row["observed"])
        result = reconcile_orders(expected, observed)
        print(f"{result.order_id}: {'MATCH' if result.matched else 'DISCREPANCY'}; human review: {result.human_review_required}")
        for discrepancy in result.discrepancies:
            print(f"  {discrepancy.severity} {discrepancy.field}: expected={discrepancy.expected_value!r}, observed={discrepancy.observed_value!r} — {discrepancy.reason}")

if __name__ == "__main__":
    main()
