# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.compliance import (
    AuditContentMode,
    ComplianceConfig,
    IntegrityConfig,
    IntegrityLevel,
)


def test_audit_content_mode_off() -> None:
    """Edge Case: AuditContentMode.OFF."""
    config = IntegrityConfig(input_mode=AuditContentMode.OFF, output_mode=AuditContentMode.OFF)
    assert config.input_mode == AuditContentMode.OFF
    assert config.output_mode == AuditContentMode.OFF


def test_integrity_level_none_with_reference() -> None:
    """Edge Case: IntegrityLevel.NONE with AuditContentMode.REFERENCE_ONLY.
    This is valid: you can store references without requiring cryptographic anchoring."""
    config = IntegrityConfig(input_mode=AuditContentMode.REFERENCE_ONLY, integrity_level=IntegrityLevel.NONE)
    assert config.input_mode == AuditContentMode.REFERENCE_ONLY
    assert config.integrity_level == IntegrityLevel.NONE


def test_invalid_hash_algorithm() -> None:
    """Edge Case: Invalid hash_algorithm string.
    Currently, validation logic for hash_algorithm is not strictly enforced in the schema beyond being a string.
    If/When we add validation, this test will fail and need updating."""
    config = IntegrityConfig(hash_algorithm="md5")  # Valid Pydantic string, though weak crypto
    assert config.hash_algorithm == "md5"

    # Testing type mismatch
    with pytest.raises(ValidationError):
        IntegrityConfig(hash_algorithm=123)  # type: ignore[arg-type]


def test_empty_compliance_config_partial_integrity() -> None:
    """Edge Case: Empty ComplianceConfig with partial IntegrityConfig overrides."""
    # Override only one field in IntegrityConfig
    integrity = IntegrityConfig(integrity_level=IntegrityLevel.DIGITAL_SIGNATURE)
    config = ComplianceConfig(integrity=integrity)

    assert config.integrity.integrity_level == IntegrityLevel.DIGITAL_SIGNATURE
    # Defaults should still hold
    assert config.integrity.input_mode == AuditContentMode.FULL_PAYLOAD
    assert config.integrity.output_mode == AuditContentMode.FULL_PAYLOAD


def test_mixed_modes() -> None:
    """Edge Case: Mixed Input/Output modes."""
    config = IntegrityConfig(input_mode=AuditContentMode.FULL_PAYLOAD, output_mode=AuditContentMode.REFERENCE_ONLY)
    assert config.input_mode == AuditContentMode.FULL_PAYLOAD
    assert config.output_mode == AuditContentMode.REFERENCE_ONLY


def test_frozen_integrity_config() -> None:
    """Edge Case: IntegrityConfig is frozen."""
    config = IntegrityConfig()
    with pytest.raises(ValidationError):
        config.input_mode = AuditContentMode.OFF  # type: ignore[attr-defined]
