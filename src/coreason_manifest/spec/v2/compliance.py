# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import StrEnum

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel


class AuditLevel(StrEnum):
    """The depth of the audit trail required."""

    NONE = "none"  # No persistent logging
    BASIC = "basic"  # Inputs/Outputs only
    FULL = "full"  # Full reasoning trace + tool inputs/outputs
    GXP_COMPLIANT = "gxp"  # Full trace + signatures + immutable archiving


class RetentionPolicy(StrEnum):
    """How long the audit artifacts must be retained."""

    EPHEMERAL = "ephemeral"  # Delete after session
    THIRTY_DAYS = "30_days"
    ONE_YEAR = "1_year"
    SEVEN_YEARS = "7_years"  # Standard for financial/legal


class AuditContentMode(StrEnum):
    """
    Determines how payload data is preserved in the audit trail.
    Harvested from Coreason-Veritas 'Zero-Copy' logic.
    """

    FULL_PAYLOAD = "full_payload"  # Store the actual JSON content (Standard)
    REDACTED = "redacted"  # Store content, but run PII scrubbers first
    REFERENCE_ONLY = "reference_only"  # ZERO-COPY: Store only the hash/pointer to external storage
    OFF = "off"  # Do not audit this payload (Metadata only)


class IntegrityLevel(StrEnum):
    """
    The cryptographic strength required for the audit trail.
    Harvested from Coreason-Veritas 'Anchoring' logic.
    """

    NONE = "none"  # No cryptographic verification
    CHECKSUM = "checksum"  # Standard SHA-256 hashing of payloads
    DIGITAL_SIGNATURE = "signature"  # Asymmetric Key Signing (Non-repudiation)
    BLOCKCHAIN_ANCHOR = "anchor"  # Immutable public/private ledger anchoring


class IntegrityConfig(CoReasonBaseModel):
    """Configuration for Zero-Copy auditing and Verification logic."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Granular control for inputs vs outputs
    input_mode: AuditContentMode = Field(
        AuditContentMode.FULL_PAYLOAD, description="How to handle user/system inputs in the audit log."
    )
    output_mode: AuditContentMode = Field(
        AuditContentMode.FULL_PAYLOAD, description="How to handle agent outputs in the audit log."
    )

    # Verification Requirements
    integrity_level: IntegrityLevel = Field(
        IntegrityLevel.NONE, description="Cryptographic proof requirement for the execution trace."
    )

    # Technical settings
    hash_algorithm: str = Field(
        "sha256", description="Algorithm used for generating payload references (if mode is reference_only)."
    )


class ComplianceConfig(CoReasonBaseModel):
    """Configuration for the Coreason Auditor."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    audit_level: AuditLevel = Field(AuditLevel.BASIC, description="Depth of logging.")
    retention: RetentionPolicy = Field(RetentionPolicy.THIRTY_DAYS, description="Data retention requirement.")

    # Artifact Generation Flags
    generate_aibom: bool = Field(False, description="Generate an AI Bill of Materials (software supply chain).")
    generate_pdf_report: bool = Field(False, description="Generate a human-readable PDF report of the session.")
    require_signature: bool = Field(False, description="Cryptographically sign the final output.")

    # PII/Sensitivity
    mask_pii: bool = Field(True, description="Attempt to scrub PII from logs before archiving.")

    # --- New Field for Veritas Harvesting ---
    integrity: IntegrityConfig = Field(
        default_factory=IntegrityConfig,
        description="Configuration for Zero-Copy auditing and data integrity verification.",
    )
