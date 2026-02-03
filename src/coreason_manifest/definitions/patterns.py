# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import ConfigDict, Field
from typing_extensions import Annotated

from coreason_manifest.common import CoReasonBaseModel


class PatternType(str, Enum):
    """The architectural pattern type."""

    SWARM = "swarm"
    HIERARCHICAL_TEAM = "hierarchical_team"
    ROUTER_SOLVER = "router_solver"


class SwarmPattern(CoReasonBaseModel):
    """Defines a flat group of agents working together.

    Attributes:
        type: The pattern type (must be 'swarm').
        participants: List of Agent IDs or references.
        handoff_mode: Mode of handoff (e.g., 'shared_scratchpad', 'direct_message').
        max_turns: Maximum number of turns.
        voting_mechanism: Optional voting mechanism (e.g., 'consensus', 'majority').
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal[PatternType.SWARM] = Field(PatternType.SWARM, description="Discriminator for SwarmPattern.")
    participants: List[str] = Field(..., description="List of Agent IDs or references.")
    handoff_mode: str = Field(..., description="Mode of handoff (e.g., 'shared_scratchpad', 'direct_message').")
    max_turns: int = Field(..., description="Maximum number of turns.")
    voting_mechanism: Optional[str] = Field(
        None, description="Optional voting mechanism (e.g., 'consensus', 'majority')."
    )


class HierarchicalTeamPattern(CoReasonBaseModel):
    """Defines a strict manager-worker structure.

    Attributes:
        type: The pattern type (must be 'hierarchical_team').
        manager_id: The Agent ID of the manager.
        workers: List of Agent IDs for the workers.
        escalation_policy: Policy for escalating issues to the manager.
        delegation_depth: Maximum depth of delegation.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal[PatternType.HIERARCHICAL_TEAM] = Field(
        PatternType.HIERARCHICAL_TEAM, description="Discriminator for HierarchicalTeamPattern."
    )
    manager_id: str = Field(..., description="The Agent ID of the manager.")
    workers: List[str] = Field(..., description="List of Agent IDs for the workers.")
    escalation_policy: Optional[str] = Field(None, description="Policy for escalating issues to the manager.")
    delegation_depth: Optional[int] = Field(None, description="Maximum depth of delegation.")


# Polymorphic Container
PatternDefinition = Annotated[
    Union[SwarmPattern, HierarchicalTeamPattern],
    Field(discriminator="type", description="Polymorphic pattern definition."),
]
