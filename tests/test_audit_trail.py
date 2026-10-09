import pytest
from velvet.audit_trail import ReviewStatus, create_audit_record, record_review
from velvet.order_lifecycle import Decision, DecisionCode

def decision(review=True):
    return Decision(DecisionCode.VERSION_CONFLICT, "evt-1", "ord-1", "Stale version", human_review_required=review)

def test_review_required_decision_creates_pending_record():
    record = create_audit_record(decision(), correlation_id="corr-1", original_order_version=7)
    assert record.review_status == ReviewStatus.PENDING
    assert record.decision_code == DecisionCode.VERSION_CONFLICT

def test_non_review_decision_is_marked_not_required():
    record = create_audit_record(decision(False), correlation_id="corr-1", original_order_version=7)
    assert record.review_status == ReviewStatus.NOT_REQUIRED

def test_review_requires_identity_and_rationale():
    record = create_audit_record(decision(), correlation_id="corr-1", original_order_version=7)
    with pytest.raises(ValueError):
        record_review(record, reviewer_id="", status=ReviewStatus.APPROVED, rationale="ok")
    with pytest.raises(ValueError):
        record_review(record, reviewer_id="human-1", status=ReviewStatus.APPROVED, rationale=" ")

def test_disposition_does_not_rewrite_original_record():
    record = create_audit_record(decision(), correlation_id="corr-1", original_order_version=7)
    review = record_review(record, reviewer_id="human-1", status=ReviewStatus.REJECTED, rationale="Reconcile current state first")
    assert review.status == ReviewStatus.REJECTED
    assert record.review_status == ReviewStatus.PENDING
    assert record.decision_code == DecisionCode.VERSION_CONFLICT

def test_cannot_review_record_that_does_not_require_review():
    record = create_audit_record(decision(False), correlation_id="corr-1", original_order_version=7)
    with pytest.raises(ValueError):
        record_review(record, reviewer_id="human-1", status=ReviewStatus.APPROVED, rationale="ok")
