# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.definitions.patterns import (
    HierarchicalTeamPattern,
    PatternDefinition,
    PatternType,
    SwarmPattern,
)


def test_pattern_type_enum() -> None:
    """Test PatternType enum values."""
    # Use Any to avoid mypy overlapping comparison error for Literals
    assert str(PatternType.SWARM.value) == "swarm"
    assert str(PatternType.HIERARCHICAL_TEAM.value) == "hierarchical_team"
    assert str(PatternType.ROUTER_SOLVER.value) == "router_solver"


def test_swarm_pattern_creation() -> None:
    """Test creating a valid SwarmPattern."""
    pattern = SwarmPattern(
        type=PatternType.SWARM,
        participants=["agent1", "agent2"],
        handoff_mode="shared_scratchpad",
        max_turns=10,
        voting_mechanism="consensus",
    )
    assert pattern.type == PatternType.SWARM
    assert pattern.participants == ["agent1", "agent2"]
    assert pattern.max_turns == 10
    assert pattern.voting_mechanism == "consensus"


def test_hierarchical_team_pattern_creation() -> None:
    """Test creating a valid HierarchicalTeamPattern."""
    pattern = HierarchicalTeamPattern(
        type=PatternType.HIERARCHICAL_TEAM,
        manager_id="manager1",
        workers=["worker1", "worker2"],
        escalation_policy="always",
        delegation_depth=2,
    )
    assert pattern.type == PatternType.HIERARCHICAL_TEAM
    assert pattern.manager_id == "manager1"
    assert len(pattern.workers) == 2
    assert pattern.delegation_depth == 2


def test_pattern_polymorphism_swarm() -> None:
    """Test polymorphic validation for SwarmPattern."""
    adapter: TypeAdapter[PatternDefinition] = TypeAdapter(PatternDefinition)
    data = {
        "type": "swarm",
        "participants": ["a1", "a2"],
        "handoff_mode": "direct",
        "max_turns": 5,
    }
    pattern = adapter.validate_python(data)
    assert isinstance(pattern, SwarmPattern)


def test_pattern_polymorphism_hierarchical() -> None:
    """Test polymorphic validation for HierarchicalTeamPattern."""
    adapter: TypeAdapter[PatternDefinition] = TypeAdapter(PatternDefinition)
    data = {
        "type": "hierarchical_team",
        "manager_id": "m1",
        "workers": ["w1"],
    }
    pattern = adapter.validate_python(data)
    assert isinstance(pattern, HierarchicalTeamPattern)


def test_invalid_pattern_discriminator() -> None:
    """Test invalid discriminator raises ValidationError."""
    adapter: TypeAdapter[PatternDefinition] = TypeAdapter(PatternDefinition)
    data = {
        "type": "invalid_pattern",
        "participants": [],
    }
    with pytest.raises(ValidationError) as excinfo:
        adapter.validate_python(data)
    assert "Input tag 'invalid_pattern' found using 'type' does not match any of the expected tags" in str(
        excinfo.value
    )


def test_swarm_pattern_extra_forbid() -> None:
    """Test that extra fields are forbidden in SwarmPattern."""
    with pytest.raises(ValidationError):
        SwarmPattern(
            type=PatternType.SWARM,
            participants=["a1"],
            handoff_mode="mode",
            max_turns=1,
            extra_field="fail",  # type: ignore[call-arg]
        )


def test_hierarchical_team_pattern_extra_forbid() -> None:
    """Test that extra fields are forbidden in HierarchicalTeamPattern."""
    with pytest.raises(ValidationError):
        HierarchicalTeamPattern(
            type=PatternType.HIERARCHICAL_TEAM,
            manager_id="m1",
            workers=["w1"],
            extra_field="fail",  # type: ignore[call-arg]
        )
