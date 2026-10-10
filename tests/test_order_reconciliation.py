import pytest
from velvet.order_reconciliation import OrderSnapshot, DiscrepancySeverity, reconcile_orders

def snapshot(**overrides):
    values = {"order_id":"ord-01", "status":"PROCESSING", "total_minor_units":1299, "currency":"EUR", "item_count":2, "source":"order_service"}
    values.update(overrides)
    return OrderSnapshot(**values)

def test_none_snapshots_fail_closed():
    result = reconcile_orders(None, None)
    assert result.valid is False
    assert result.matched is False
    assert result.human_review_required is True

def test_matching_snapshots_have_no_discrepancies():
    result = reconcile_orders(snapshot(), snapshot(source="warehouse_feed"))
    assert result.matched is True
    assert result.discrepancies == ()
    assert result.human_review_required is False

def test_status_mismatch_is_high_severity_and_requires_review():
    result = reconcile_orders(snapshot(), snapshot(status="SHIPPED"))
    assert result.matched is False
    assert result.discrepancies[0].field == "status"
    assert result.discrepancies[0].severity == DiscrepancySeverity.HIGH
    assert result.human_review_required is True

def test_item_count_mismatch_is_medium_severity():
    result = reconcile_orders(snapshot(), snapshot(item_count=3))
    assert result.discrepancies[0].severity == DiscrepancySeverity.MEDIUM
    assert result.human_review_required is False

def test_multiple_discrepancies_are_all_reported():
    result = reconcile_orders(snapshot(), snapshot(status="SHIPPED", total_minor_units=1399, item_count=3))
    assert {d.field for d in result.discrepancies} == {"status", "total_minor_units", "item_count"}

def test_different_order_ids_fail_closed():
    result = reconcile_orders(snapshot(), snapshot(order_id="ord-02"))
    assert result.valid is False
    assert result.human_review_required is True
    assert result.discrepancies == ()

@pytest.mark.parametrize("overrides", [{"total_minor_units":-1}, {"total_minor_units":True}, {"item_count":-1}, {"currency":"EURO"}, {"status":""}])
def test_invalid_snapshot_fails_closed(overrides):
    result = reconcile_orders(snapshot(), snapshot(**overrides))
    assert result.valid is False
    assert result.human_review_required is True

def test_currency_mismatch_is_high_severity():
    result = reconcile_orders(snapshot(), snapshot(currency="USD"))
    assert result.discrepancies[0].field == "currency"
    assert result.human_review_required is True
