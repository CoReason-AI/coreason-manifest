# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Dict, List, Literal, Optional

from pydantic import ConfigDict

from coreason_manifest.spec.common_base import ManifestBaseModel
from coreason_manifest.spec.core.nodes import Node


class FlowMetadata(ManifestBaseModel):
    """Standard metadata."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: str
    version: str
    description: Optional[str] = None


class FlowInterface(ManifestBaseModel):
    """Input/Output JSON schema contract."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    inputs: Dict[str, str]
    outputs: Dict[str, str]


class Blackboard(ManifestBaseModel):
    """Shared memory schema."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_definition: Dict[str, str]


class Step(ManifestBaseModel):
    """A single unit in a linear sequence."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    node: Node


class LinearFlow(ManifestBaseModel):
    """A deterministic, ordered list of steps (Script)."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["LinearFlow"]
    metadata: FlowMetadata
    interface: FlowInterface
    sequence: List[Step]


class Graph(ManifestBaseModel):
    """Contains nodes and edges."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    nodes: List[Node]
    edges: List[Dict[str, str]]


class GraphFlow(ManifestBaseModel):
    """A cyclic, branching network of nodes (System)."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["GraphFlow"]
    metadata: FlowMetadata
    interface: FlowInterface
    graph: Graph
    blackboard: Optional[Blackboard] = None
