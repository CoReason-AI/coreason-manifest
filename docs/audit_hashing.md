# Audit Hashing & Integrity

Coreason's audit system implements a **Tamper-Evident** design compliant with EU AI Act Article 12. This ensures that every audit log entry is cryptographically bound to its content and, when chained, to the entire history of the audit trail.

## The Model: `AuditLog`

The `AuditLog` model (defined in `coreason_manifest.spec.common.observability`) is the fundamental unit of compliance. It contains:

1.  **Identity & Lineage:** `id`, `request_id`, `root_request_id`.
2.  **Context:** `timestamp`, `actor`, `action`, `outcome`.
3.  **Safety Metadata:** Optional data regarding policy enforcement.
4.  **Cryptographic Bindings:** `integrity_hash` and `previous_hash`.

## Hashing Algorithm

The `compute_audit_hash` function generates a deterministic SHA-256 hash.

### Canonicalization Rules

To ensure consistent hashing across different environments and JSON parsers, we enforce the following rules:

1.  **Field Selection:** Only specific business fields are included.
    *   Included: `id`, `request_id`, `root_request_id`, `timestamp`, `actor`, `action`, `outcome`, `previous_hash`, `safety_metadata`.
    *   **Excluded:** `integrity_hash` (self-referential).
    *   **Excluded:** Any field with a `None` value.
2.  **Type Normalization:**
    *   `UUID`: Converted to string.
    *   `datetime`: Converted to ISO 8601 string in **UTC**. If the object is timezone-naive, it is assumed to be UTC.
3.  **Serialization:**
    *   Format: JSON.
    *   Keys: Sorted alphabetically (`sort_keys=True`).
    *   Encoding: UTF-8.
    *   ASCII Escaping: Disabled (`ensure_ascii=False`) to preserve Unicode characters (e.g., in names or actions) exactly as they are.

### Usage Example

```python
from uuid import uuid4
from datetime import datetime, timezone
from coreason_manifest.utils.audit import compute_audit_hash

data = {
    "id": uuid4(),
    "request_id": uuid4(),
    "root_request_id": uuid4(),
    "timestamp": datetime.now(timezone.utc),
    "actor": "system",
    "action": "policy_check",
    "outcome": "approved",
    "previous_hash": "a1b2c3d4..."
}

# Compute the hash
hash_val = compute_audit_hash(data)
print(f"SHA-256: {hash_val}")
```

## Chain Verification

The `verify_chain` utility validates a sequence of `AuditLog` entries to detect tampering.

### Verification Logic

For a list of logs `[L0, L1, L2, ...]`:

1.  **Integrity Check:** For every log `Ln`, `compute_audit_hash(Ln)` must equal `Ln.integrity_hash`. This proves the individual record hasn't been modified.
2.  **Chain Check:** For every log `Ln` (where `n > 0`), `Ln.previous_hash` must equal `L(n-1).integrity_hash`. This proves the sequence hasn't been reordered or cut.

### Usage Example

```python
from coreason_manifest.utils.audit import verify_chain
from coreason_manifest import AuditLog

# Assume 'logs' is a list of AuditLog objects fetched from storage
is_valid = verify_chain(logs)

if is_valid:
    print("Audit trail is intact.")
else:
    print("TAMPERING DETECTED: The chain is broken or corrupted.")
```

## Edge Cases & Security Notes

*   **Unicode:** The hashing logic handles full Unicode support. Do not rely on ASCII escaping for sanitization.
*   **Timezones:** Always store and hash timestamps in UTC. Local times will cause hash mismatches if the timezone offset is lost or changed.
*   **Nulls:** Adding a field with a `None` value is cryptographically equivalent to the field being missing.
