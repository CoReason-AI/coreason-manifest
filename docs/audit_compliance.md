# Audit & Compliance

This document details the audit logging architecture, designed to comply with the EU AI Act (Article 12) and ensure data integrity.

## Regulatory Compliance

The `AuditLog` structure provides a tamper-evident legal record of agent actions.

### AuditLog

- **id** (`UUID`): Unique identifier.
- **timestamp** (`datetime`): ISO8601 timestamp.
- **actor** (`str`): User ID or Agent Component ID.
- **event_type** (`AuditEventType`): Type of event (`system_change`, `prediction`, `guardrail_trigger`).
- **safety_metadata** (`Dict[str, Any]`): Safety metadata (e.g., PII detected, toxicity score).
- **previous_hash** (`str`): Hash of the previous log entry.
- **integrity_hash** (`str`): SHA256 hash of this record + `previous_hash`.

## Chain of Custody & Integrity

### Hashing Mechanism

Each `AuditLog` entry includes a `previous_hash` field, linking it to the preceding entry in a blockchain-like manner. This ensures that any alteration to a past record invalidates the chain.

The `integrity_hash` is computed using the `compute_hash()` method, which generates a SHA256 hash of the record's content (excluding the hash itself) combined with the `previous_hash`.
