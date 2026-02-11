# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Dict, Optional

from pydantic import ConfigDict

from coreason_manifest.spec.common_base import ManifestBaseModel
from coreason_manifest.spec.core.engines import Optimizer, ReasoningEngine, Reflex, Supervision


class Node(ManifestBaseModel):
    """Base class for all nodes."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    id: str
    metadata: Dict[str, str] = {}
    supervision: Optional[Supervision] = None


class AgentBrain(ManifestBaseModel):
    """Defines the cognitive profile of an agent."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    role: str
    reasoning: Optional[ReasoningEngine] = None
    reflex: Optional[Reflex] = None


class AgentNode(Node):
    """Executes an AgentBrain."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    brain: AgentBrain


class SwitchNode(Node):
    """Routes execution based on a variable."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    variable: str
    cases: Dict[str, str]
    default: Optional[str] = None


class PlannerNode(Node):
    """Dynamically solves a goal using an Optimizer."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    goal: str
    optimizer: Optimizer


class HumanNode(Node):
    """Pauses for human intervention."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    prompt: str


class Placeholder(ManifestBaseModel):
    """An abstract slot for an agent to be injected later."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    ref: str
