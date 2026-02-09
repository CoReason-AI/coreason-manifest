# Compliance & Audit Schema

Coreason V2 introduces a dedicated **Compliance Layer** (`ComplianceConfig`) to the Recipe Manifest. This schema allows a Recipe to dictate the rigor of the audit trail, instructing the `coreason-auditor` worker on what artifacts to generate (e.g., for GxP, SOC2, or casual usage).

## Purpose

Different workflows have different regulatory requirements:
*   **Casual Chat:** Needs minimal logging and short retention.
*   **Customer Support:** Needs PII scrubbing and 30-day retention.
*   **Clinical Decision Support (GxP):** Needs full reasoning traces, cryptographic signatures, unmasked data (for clinical context), and long-term retention (7+ years).

The `ComplianceConfig` schema standardizes these requirements within the manifest itself.

## Configuration Reference

The `ComplianceConfig` model is located at `src/coreason_manifest/spec/v2/compliance.py`.

```python
from coreason_manifest.spec.v2.compliance import (
    ComplianceConfig,
    AuditLevel,
    RetentionPolicy,
    IntegrityConfig,
    AuditContentMode,
    IntegrityLevel
)

config = ComplianceConfig(
    audit_level=AuditLevel.BASIC,
    retention=RetentionPolicy.THIRTY_DAYS,
    generate_aibom=False,
    generate_pdf_report=False,
    require_signature=False,
    mask_pii=True,
    # New in V2 (Veritas Harvest)
    integrity=IntegrityConfig(
        input_mode=AuditContentMode.FULL_PAYLOAD,
        output_mode=AuditContentMode.REFERENCE_ONLY,
        integrity_level=IntegrityLevel.CHECKSUM
    )
)
```

### 1. Audit Levels (`AuditLevel`)

Controls *what* is logged during execution.

| Level | Value | Description | Use Case |
| :--- | :--- | :--- | :--- |
| **NONE** | `"none"` | No persistent logging. | Ephemeral chats, testing. |
| **BASIC** | `"basic"` | Logs Inputs and Outputs only. | Standard SaaS features. |
| **FULL** | `"full"` | Logs full reasoning trace (CoT), tool inputs/outputs, and intermediate steps. | Debugging, complex reasoning. |
| **GXP** | `"gxp"` | Full trace + Signatures + Immutable Archiving + Metadata hashing. | FDA/GxP, Financial, Legal. |

### 2. Retention Policy (`RetentionPolicy`)

Controls *how long* the audit artifacts must be retained by the storage backend.

| Policy | Value | Description |
| :--- | :--- | :--- |
| **EPHEMERAL** | `"ephemeral"` | Deleted immediately after the session ends. |
| **30 DAYS** | `"30_days"` | Standard rolling window. |
| **1 YEAR** | `"1_year"` | Annual audit compliance. |
| **7 YEARS** | `"7_years"` | Legal/Financial standard (e.g., tax records, clinical trials). |

### 3. Artifact Generation Flags

| Flag | Default | Description |
| :--- | :--- | :--- |
| `generate_aibom` | `False` | Generates an **AI Bill of Materials** (software supply chain), listing all models, tools, and plugins used. |
| `generate_pdf_report` | `False` | Generates a human-readable PDF summary of the session. |
| `require_signature` | `False` | Cryptographically signs the final output using the worker's private key. |

### 4. Privacy (`mask_pii`)

*   `mask_pii` (bool, default `True`): If `True`, the Auditor will attempt to scrub Personally Identifiable Information (PII) from logs before archiving.
*   **Important:** For GxP or Clinical use cases, you often set this to `False` because the patient context is critical for the audit trail and is protected by other means (HIPAA-compliant storage).

### 5. Data Integrity & Zero-Copy Auditing (`IntegrityConfig`)

Harvested from Coreason-Veritas, these settings control payload storage and verification.

#### Audit Content Mode (`AuditContentMode`)

Controls how the input/output payloads are stored in the log.

| Mode | Value | Description | Use Case |
| :--- | :--- | :--- | :--- |
| **FULL PAYLOAD** | `"full_payload"` | Store the actual JSON content (Standard). | Standard Debugging. |
| **REDACTED** | `"redacted"` | Store content, but run PII scrubbers first. | Privacy Compliance. |
| **REFERENCE ONLY** | `"reference_only"` | **ZERO-COPY:** Store only a hash/pointer to external storage. | High Volume / High Security. |
| **OFF** | `"off"` | Do not audit this payload (Metadata only). | Ephemeral data. |

#### Integrity Level (`IntegrityLevel`)

Controls the cryptographic strength of the audit trail.

| Level | Value | Description | Use Case |
| :--- | :--- | :--- | :--- |
| **NONE** | `"none"` | No cryptographic verification. | Standard logging. |
| **CHECKSUM** | `"checksum"` | SHA-256 hashing of payloads. | Data Integrity checks. |
| **DIGITAL SIGNATURE** | `"signature"` | Asymmetric Key Signing (Non-repudiation). | Legal/Contracts. |
| **BLOCKCHAIN ANCHOR** | `"anchor"` | Immutable public/private ledger anchoring. | GxP / Financial Audits. |

## Examples

### Scenario A: Casual Chatbot

Minimal overhead.

```python
compliance = ComplianceConfig(
    audit_level=AuditLevel.NONE,
    retention=RetentionPolicy.EPHEMERAL
)
```

### Scenario B: Financial Advisor

Strict logging, long retention, but PII must be masked.

```python
compliance = ComplianceConfig(
    audit_level=AuditLevel.FULL,
    retention=RetentionPolicy.SEVEN_YEARS,
    mask_pii=True,
    require_signature=True
)
```

### Scenario C: Clinical Trial Analysis (GxP)

Maximum rigor. Data integrity is paramount, so signatures and AIBOM are required. PII masking might be disabled if the system operates within a secure enclave.

```python
compliance = ComplianceConfig(
    audit_level=AuditLevel.GXP_COMPLIANT,
    retention=RetentionPolicy.SEVEN_YEARS,
    generate_aibom=True,
    generate_pdf_report=True,
    mask_pii=False, # Keep clinical data intact
    integrity=IntegrityConfig(
        integrity_level=IntegrityLevel.BLOCKCHAIN_ANCHOR
    )
)
```
