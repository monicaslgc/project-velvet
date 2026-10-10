import pytest
from velvet.exception_triage import ExceptionCategory, OrderException, Priority, triage_exception

def exception(**overrides):
    data = {"exception_id": "exc-001", "order_id": "ord-001", "category": "SHIPMENT_DELAY", "age_hours": 2}
    data.update(overrides)
    return OrderException(**data)

def test_none_exception_fails_closed():
    result = triage_exception(None)
    assert result.assigned_team == "manual_review"
    assert result.human_review_required is True
    assert result.valid is False

def test_low_risk_exception_routes_to_category_owner():
    result = triage_exception(exception())
    assert result.priority == Priority.P3
    assert result.assigned_team == "fulfilment_operations"
    assert result.valid is True
    assert result.human_review_required is False
    assert result.reasons

def test_customer_impact_and_age_12_hours_is_p2():
    result = triage_exception(exception(age_hours=12, customer_impact=True))
    assert result.priority == Priority.P2
    assert "Customer impact is flagged." in result.reasons

@pytest.mark.parametrize("overrides", [
    {"financial_risk": True}, {"repeat_count": 3}, {"customer_impact": True, "age_hours": 24},
])
def test_p1_conditions_require_human_review(overrides):
    result = triage_exception(exception(**overrides))
    assert result.priority == Priority.P1
    assert result.human_review_required is True

def test_repeated_exception_is_explained():
    result = triage_exception(exception(repeat_count=3))
    assert any("occurred 3 times" in reason for reason in result.reasons)

def test_unknown_category_fails_to_manual_review():
    result = triage_exception(exception(category="MYSTERY"))
    assert result.assigned_team == "manual_review"
    assert result.human_review_required is True
    assert result.priority == Priority.P2

@pytest.mark.parametrize("overrides", [
    {"age_hours": -1}, {"age_hours": True}, {"age_hours": float("nan")},
    {"age_hours": float("inf")}, {"age_hours": float("-inf")}, {"repeat_count": 1.5},
    {"repeat_count": 0}, {"repeat_count": True}, {"customer_impact": "yes"},
])
def test_invalid_payload_fails_closed(overrides):
    result = triage_exception(exception(**overrides))
    assert result.valid is False
    assert result.assigned_team == "manual_review"
    assert result.human_review_required is True
    assert result.priority == Priority.P1

def test_category_mapping_covers_supported_exception_types():
    expected = {
        ExceptionCategory.PAYMENT_DELAY: "payments_operations",
        ExceptionCategory.INVENTORY_MISMATCH: "inventory_operations",
        ExceptionCategory.SHIPMENT_DELAY: "fulfilment_operations",
        ExceptionCategory.ADDRESS_VALIDATION: "customer_operations",
    }
    for category, team in expected.items():
        result = triage_exception(exception(category=category.value))
        assert result.assigned_team == team
