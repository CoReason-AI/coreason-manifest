# Copyright (c) 2025 CoReason, Inc.

import pytest
from pydantic import BaseModel, ValidationError

from coreason_manifest.definitions.patterns import (
    HierarchicalTeamPattern,
    PatternDefinition,
    PatternType,
    SwarmPattern,
)


class PatternContainer(BaseModel):
    pattern: PatternDefinition


def test_swarm_pattern_creation() -> None:
    """Test creating a valid SwarmPattern."""
    swarm = SwarmPattern(
        type=PatternType.SWARM,
        participants=["agent_a", "agent_b"],
        handoff_mode="shared_scratchpad",
        max_turns=10,
        voting_mechanism="consensus",
    )
    assert swarm.type == PatternType.SWARM
    assert swarm.participants == ["agent_a", "agent_b"]
    assert swarm.handoff_mode == "shared_scratchpad"
    assert swarm.max_turns == 10
    assert swarm.voting_mechanism == "consensus"


def test_swarm_pattern_defaults() -> None:
    """Test SwarmPattern defaults (voting_mechanism is optional)."""
    swarm = SwarmPattern(
        type=PatternType.SWARM,
        participants=["agent_a"],
        handoff_mode="direct",
        max_turns=5,
    )
    assert swarm.voting_mechanism is None


def test_hierarchical_team_pattern_creation() -> None:
    """Test creating a valid HierarchicalTeamPattern."""
    team = HierarchicalTeamPattern(
        type=PatternType.HIERARCHICAL_TEAM,
        manager_id="manager_agent",
        workers=["worker_1", "worker_2"],
        escalation_policy="always_escalate",
        delegation_depth=2,
    )
    assert team.type == PatternType.HIERARCHICAL_TEAM
    assert team.manager_id == "manager_agent"
    assert len(team.workers) == 2
    assert team.escalation_policy == "always_escalate"
    assert team.delegation_depth == 2


def test_hierarchical_team_defaults() -> None:
    """Test HierarchicalTeamPattern optional fields."""
    team = HierarchicalTeamPattern(
        type=PatternType.HIERARCHICAL_TEAM,
        manager_id="manager",
        workers=[],
    )
    assert team.escalation_policy is None
    assert team.delegation_depth is None


def test_polymorphism_swarm() -> None:
    """Test that PatternDefinition correctly resolves to SwarmPattern."""
    data = {
        "pattern": {
            "type": "swarm",
            "participants": ["a"],
            "handoff_mode": "test",
            "max_turns": 1,
        }
    }
    container = PatternContainer(**data)
    assert isinstance(container.pattern, SwarmPattern)


def test_polymorphism_hierarchical() -> None:
    """Test that PatternDefinition correctly resolves to HierarchicalTeamPattern."""
    data = {
        "pattern": {
            "type": "hierarchical_team",
            "manager_id": "mgr",
            "workers": ["w1"],
        }
    }
    container = PatternContainer(**data)
    assert isinstance(container.pattern, HierarchicalTeamPattern)


def test_invalid_pattern_discriminator() -> None:
    """Test that an invalid type raises a validation error."""
    data = {
        "pattern": {
            "type": "unknown_pattern",
            "participants": [],
        }
    }
    with pytest.raises(ValidationError) as exc:
        PatternContainer(**data)
    # Pydantic V2 error message for discriminated union
    assert "Input tag 'unknown_pattern' found using 'type' does not match any of the expected tags" in str(exc.value)


def test_pattern_extra_forbid() -> None:
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError):
        SwarmPattern(
            type=PatternType.SWARM,
            participants=[],
            handoff_mode="x",
            max_turns=1,
            extra_field="fail",  # type: ignore[call-arg]
        )
