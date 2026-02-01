# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.definitions.agent import (
    ObservabilityConfig,
    PolicyConfig,
    TraceLevel,
)


def test_policy_config_empty_collections() -> None:
    """Test PolicyConfig with empty collections."""
    policy = PolicyConfig(budget_caps={}, human_in_the_loop=[], allowed_domains=[])
    assert policy.budget_caps == {}
    assert policy.human_in_the_loop == []


def test_observability_config_none_level() -> None:
    """Test TraceLevel.NONE."""
    obs = ObservabilityConfig(trace_level=TraceLevel.NONE)
    assert obs.trace_level == TraceLevel.NONE


def test_observability_config_enums_are_strings() -> None:
    """Test that Enum values are serialized as strings."""
    obs = ObservabilityConfig(trace_level=TraceLevel.FULL)
    dumped = obs.model_dump()
    assert dumped["trace_level"] == "full"
    assert isinstance(dumped["trace_level"], str)
