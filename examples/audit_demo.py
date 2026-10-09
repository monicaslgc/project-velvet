"""Minimal synthetic audit + human-review example."""
from velvet.audit_trail import ReviewStatus, create_audit_record, record_review
from velvet.order_lifecycle import Decision, DecisionCode

decision = Decision(DecisionCode.VERSION_CONFLICT, "evt-review-01", "ord-demo-10", "Order version is stale.", human_review_required=True)
record = create_audit_record(decision, correlation_id="corr-demo-01", original_order_version=4)
review = record_review(record, reviewer_id="reviewer-demo", status=ReviewStatus.REJECTED, rationale="Re-read authoritative order state before retrying.")
print(f"audit={record.audit_id} decision={record.decision_code} review={review.status}")
print("Original decision preserved; no order mutation or external side effect was performed.")
