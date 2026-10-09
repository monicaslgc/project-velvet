"""Immutable audit values and human-review metadata for a portfolio demo."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4
from .order_lifecycle import Decision, DecisionCode

class ReviewStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

@dataclass(frozen=True)
class AuditRecord:
    audit_id: str
    event_id: str | None
    order_id: str | None
    decision_code: DecisionCode
    decision_reason: str
    review_status: ReviewStatus
    created_at: str
    correlation_id: str
    original_order_version: int | None

@dataclass(frozen=True)
class ReviewDisposition:
    audit_id: str
    status: ReviewStatus
    reviewer_id: str
    reviewed_at: str
    rationale: str

def create_audit_record(decision: Decision, *, correlation_id: str, original_order_version: int | None) -> AuditRecord:
    if not isinstance(correlation_id, str) or not correlation_id.strip():
        raise ValueError("correlation_id is required")
    needs_review = decision.human_review_required
    return AuditRecord(audit_id=str(uuid4()), event_id=decision.event_id, order_id=decision.order_id, decision_code=decision.code, decision_reason=decision.reason, review_status=ReviewStatus.PENDING if needs_review else ReviewStatus.NOT_REQUIRED, created_at=datetime.now(timezone.utc).isoformat(), correlation_id=correlation_id, original_order_version=original_order_version)

def record_review(record: AuditRecord, *, reviewer_id: str, status: ReviewStatus, rationale: str, reviewed_at: str | None = None) -> ReviewDisposition:
    """Record a disposition separately; it never mutates the original audit record."""
    if record.review_status != ReviewStatus.PENDING:
        raise ValueError("Only records pending review can receive a disposition")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise ValueError("reviewer_id is required")
    if status not in (ReviewStatus.APPROVED, ReviewStatus.REJECTED):
        raise ValueError("status must be APPROVED or REJECTED")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("rationale is required")
    return ReviewDisposition(record.audit_id, status, reviewer_id, reviewed_at or datetime.now(timezone.utc).isoformat(), rationale)
