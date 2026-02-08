# Data Integrity & Zero-Copy Auditing

Coreason V2 introduces **Data Integrity** and **Zero-Copy Auditing** capabilities to the Compliance Layer. These features, harvested from the legacy `coreason-veritas` system, provide granular control over *what* data is stored in the audit trail and *how* its integrity is verified.

This is critical for high-compliance environments (GxP, Finance) where storing full payloads is risky or costly, and where cryptographic proof of execution is required.

## Configuration Model

The configuration is nested within `ComplianceConfig` under the `integrity` field.

```python
from coreason_manifest.spec.v2.compliance import (
    ComplianceConfig,
    IntegrityConfig,
    AuditContentMode,
    IntegrityLevel
)

compliance = ComplianceConfig(
    integrity=IntegrityConfig(
        input_mode=AuditContentMode.FULL_PAYLOAD,
        output_mode=AuditContentMode.REFERENCE_ONLY,
        integrity_level=IntegrityLevel.CHECKSUM
    )
)
```

## 1. Zero-Copy Auditing (`AuditContentMode`)

This setting determines how input and output payloads are preserved in the audit log. It allows you to minimize storage costs and reduce privacy risks by storing references instead of raw data.

| Mode | Value | Description | Use Case |
| :--- | :--- | :--- | :--- |
| **FULL PAYLOAD** | `"full_payload"` | Stores the actual JSON content. **(Default)** | Standard debugging and auditing. |
| **REDACTED** | `"redacted"` | Stores content, but runs PII scrubbers first. | Customer support, privacy-sensitive apps. |
| **REFERENCE ONLY** | `"reference_only"` | **Zero-Copy:** Stores only a hash/pointer to external storage. | High-volume data, large artifacts (images/videos), GxP raw data handling. |
| **OFF** | `"off"` | Does not audit the payload (Metadata only). | Ephemeral interactions, extremely sensitive data. |

You can configure `input_mode` and `output_mode` independently.

## 2. Cryptographic Anchoring (`IntegrityLevel`)

This setting controls the strength of the cryptographic verification applied to the audit trail.

| Level | Value | Description | Use Case |
| :--- | :--- | :--- | :--- |
| **NONE** | `"none"` | No cryptographic verification. **(Default)** | Development, low-risk apps. |
| **CHECKSUM** | `"checksum"` | Standard SHA-256 hashing of payloads. | Basic tamper-detection. |
| **DIGITAL SIGNATURE** | `"signature"` | Asymmetric Key Signing (Non-repudiation). | Financial transactions, legal contracts. |
| **BLOCKCHAIN ANCHOR** | `"anchor"` | Immutable public/private ledger anchoring. | High-stakes GxP, inter-organizational audit trails. |

## 3. Technical Settings

*   **`hash_algorithm`**: The algorithm used for generating payload references (if mode is `reference_only`). Defaults to `"sha256"`.

## Examples

### Scenario: High-Volume Data Processing

Avoid clogging the audit logs with massive datasets by using **Reference Only** mode for outputs.

```python
compliance = ComplianceConfig(
    integrity=IntegrityConfig(
        input_mode=AuditContentMode.FULL_PAYLOAD,  # Log the small prompt
        output_mode=AuditContentMode.REFERENCE_ONLY # Link to the large result
    )
)
```

### Scenario: GxP Clinical Trial

Requires **Digital Signatures** to ensure non-repudiation of every step.

```python
compliance = ComplianceConfig(
    audit_level=AuditLevel.GXP_COMPLIANT,
    integrity=IntegrityConfig(
        integrity_level=IntegrityLevel.DIGITAL_SIGNATURE
    )
)
```
