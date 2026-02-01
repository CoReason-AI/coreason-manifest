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
from coreason_manifest.definitions.agent import ObservabilityConfig, TraceLevel
from pydantic import ValidationError


def test_observability_config_valid() -> None:
    """Test creating a valid ObservabilityConfig."""
    obs = ObservabilityConfig(
        trace_level=TraceLevel.METADATA_ONLY, retention_policy="90_days", encryption_key_id="key-123"
    )
    assert obs.trace_level == TraceLevel.METADATA_ONLY
    assert obs.retention_policy == "90_days"
    assert obs.encryption_key_id == "key-123"


def test_observability_config_defaults() -> None:
    """Test defaults for ObservabilityConfig."""
    obs = ObservabilityConfig()
    assert obs.trace_level == TraceLevel.FULL
    assert obs.retention_policy == "30_days"
    assert obs.encryption_key_id is None


def test_observability_config_invalid_trace_level() -> None:
    """Test invalid trace level."""
    with pytest.raises(ValidationError):
        ObservabilityConfig(trace_level="invalid")
