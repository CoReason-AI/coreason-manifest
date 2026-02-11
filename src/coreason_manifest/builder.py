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

from coreason_manifest.spec.core.flow import (
    AnyNode,
    Blackboard,
    Edge,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
    VariableDef,
)
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import InspectorNode
from coreason_manifest.spec.core.tools import ToolPack
from coreason_manifest.utils.validator import validate_flow


class NewLinearFlow:
    """Fluent API to construct LinearFlows programmatically."""

    def __init__(self, name: str, version: str = "0.1", description: str = "") -> None:
        self.metadata = FlowMetadata(name=name, version=version, description=description, tags=[])
        self.sequence: list[AnyNode] = []
        self.tool_packs: list[ToolPack] = []
        self.governance: Governance | None = None

    def add_step(self, node: AnyNode) -> "NewLinearFlow":
        """Appends a node to the sequence."""
        self.sequence.append(node)
        return self

    def add_inspector(
        self, id: str, target: str, criteria: str, output: str, pass_threshold: float = 0.5
    ) -> "NewLinearFlow":
        """Adds an inspector node to the sequence."""
        node = InspectorNode(
            id=id,
            metadata={},
            supervision=None,
            target_variable=target,
            criteria=criteria,
            pass_threshold=pass_threshold,
            output_variable=output,
            optimizer=None,
            type="inspector",
        )
        self.sequence.append(node)
        return self

    def add_tool_pack(self, pack: ToolPack) -> "NewLinearFlow":
        """Adds a tool pack to the flow."""
        self.tool_packs.append(pack)
        return self

    def set_governance(self, gov: Governance) -> "NewLinearFlow":
        """Sets the governance policy."""
        self.governance = gov
        return self

    def build(self) -> LinearFlow:
        """Constructs and validates the LinearFlow object."""
        flow = LinearFlow(
            kind="LinearFlow",
            metadata=self.metadata,
            sequence=self.sequence,
            tool_packs=self.tool_packs,
            governance=self.governance,
        )

        errors = validate_flow(flow)
        if errors:
            raise ValueError("Validation failed:\n- " + "\n- ".join(errors))

        return flow


class NewGraphFlow:
    """Fluent API to construct GraphFlows programmatically."""

    def __init__(self, name: str, version: str = "0.1", description: str = "") -> None:
        self.metadata = FlowMetadata(name=name, version=version, description=description, tags=[])
        self._nodes: dict[str, AnyNode] = {}
        self._edges: list[Edge] = []

        # Defaults
        self.interface = FlowInterface(inputs={}, outputs={})
        self.blackboard: Blackboard | None = None
        self.tool_packs: list[ToolPack] = []
        self.governance: Governance | None = None

    def add_node(self, node: AnyNode) -> "NewGraphFlow":
        """Adds a node to the graph."""
        self._nodes[node.id] = node
        return self

    def add_inspector(
        self, id: str, target: str, criteria: str, output: str, pass_threshold: float = 0.5
    ) -> "NewGraphFlow":
        """Adds an inspector node to the graph."""
        node = InspectorNode(
            id=id,
            metadata={},
            supervision=None,
            target_variable=target,
            criteria=criteria,
            pass_threshold=pass_threshold,
            output_variable=output,
            optimizer=None,
            type="inspector",
        )
        self._nodes[node.id] = node
        return self

    def connect(self, source: str, target: str, condition: str | None = None) -> "NewGraphFlow":
        """Adds an edge to the graph."""
        self._edges.append(Edge(source=source, target=target, condition=condition))
        return self

    def add_tool_pack(self, pack: ToolPack) -> "NewGraphFlow":
        """Adds a tool pack to the flow."""
        self.tool_packs.append(pack)
        return self

    def set_governance(self, gov: Governance) -> "NewGraphFlow":
        """Sets the governance policy."""
        self.governance = gov
        return self

    def set_interface(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> "NewGraphFlow":
        """Defines the Input/Output contract for the Flow."""
        self.interface = FlowInterface(inputs=inputs, outputs=outputs)
        return self

    def set_blackboard(self, variables: dict[str, VariableDef], persistence: bool = False) -> "NewGraphFlow":
        """Configures the shared memory blackboard."""
        self.blackboard = Blackboard(variables=variables, persistence=persistence)
        return self

    def build(self) -> GraphFlow:
        """Constructs and validates the GraphFlow object."""
        graph = Graph(nodes=self._nodes, edges=self._edges)

        flow = GraphFlow(
            kind="GraphFlow",
            metadata=self.metadata,
            interface=self.interface,
            blackboard=self.blackboard,
            graph=graph,
            tool_packs=self.tool_packs,
            governance=self.governance,
        )

        errors = validate_flow(flow)
        if errors:
            raise ValueError("Validation failed:\n- " + "\n- ".join(errors))

        return flow
