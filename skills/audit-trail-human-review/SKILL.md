# Skill: Audit Trail and Human Review

## Purpose
Capture a structured record of a policy decision and separately record a human disposition when required.

## Rules
- Preserve the original policy decision and reason.
- Require a correlation ID when creating an audit record.
- Route decisions flagged for review to `PENDING`; otherwise use `NOT_REQUIRED`.
- Require reviewer identity, an explicit approve/reject disposition, timestamp, and rationale.
- A review disposition is separate metadata; it does not rewrite the original decision and does not execute an order transition.
- This demonstration creates immutable in-memory values only. Do not describe it as durable or tamper-proof audit storage.
- Production needs append-only persistence, access controls, retention/integrity protections, and safe coordination with any authoritative state change.
