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
from coreason_manifest.definitions.agent import PolicyConfig
from pydantic import ValidationError


def test_policy_config_valid() -> None:
    """Test creating a valid PolicyConfig."""
    policy = PolicyConfig(
        budget_caps={"total_cost": 50.0, "total_tokens": 10000},
        human_in_the_loop=["node1", "node2"],
        allowed_domains=["api.example.com", "google.com"],
    )
    assert policy.budget_caps["total_cost"] == 50.0
    assert "node1" in policy.human_in_the_loop
    assert "google.com" in policy.allowed_domains


def test_policy_config_defaults() -> None:
    """Test defaults for PolicyConfig."""
    policy = PolicyConfig()
    assert policy.budget_caps == {}
    assert policy.human_in_the_loop == []
    assert policy.allowed_domains == []


def test_policy_config_immutability() -> None:
    """Test that PolicyConfig is frozen."""
    policy = PolicyConfig(budget_caps={"cost": 10.0})
    with pytest.raises(ValidationError):
        policy.human_in_the_loop = ["node1"]  # type: ignore[misc]
