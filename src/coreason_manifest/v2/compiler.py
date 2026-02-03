# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Compiler module for transforming V2 Manifests to V1 Runtime Topology."""

from typing import Any, Dict, List, Union

from coreason_manifest.definitions.agent import AgentDependencies, ToolRequirement
from coreason_manifest.definitions.topology import (
    AgentNode,
    ConditionalEdge,
    CouncilConfig,
    Edge,
    GraphTopology,
    LogicNode,
    Node,
    VisualMetadata,
)
from coreason_manifest.v2.spec.definitions import (
    AgentStep,
    CouncilStep,
    LogicStep,
    ManifestV2,
    SwitchStep,
    ToolDefinition,
)
from coreason_manifest.v2.validator import validate_strict


def _convert_visual_metadata(design_metadata: Union[Dict[str, Any], Any, None]) -> Union[VisualMetadata, None]:
    """Convert V2 design metadata to V1 visual metadata.

    Args:
        design_metadata: The design metadata from V2 (DesignMetadata object or dict).

    Returns:
        The converted V1 VisualMetadata or None.
    """
    if not design_metadata:
        return None

    # Handle if it's a Pydantic model (DesignMetadata) or dict
    data = (
        design_metadata.model_dump(by_alias=True) if hasattr(design_metadata, "model_dump") else dict(design_metadata)
    )

    return VisualMetadata(
        label=data.get("label"),
        x_y_coordinates=[data.get("x", 0.0), data.get("y", 0.0)],
        icon=data.get("icon"),
    )


def compile_dependencies(manifest: ManifestV2) -> AgentDependencies:
    """Extract tool dependencies from V2 manifest.

    Args:
        manifest: The V2 manifest.

    Returns:
        The V1 AgentDependencies object.
    """
    tools = []
    for definition in manifest.definitions.values():
        if isinstance(definition, ToolDefinition):
            tools.append(
                ToolRequirement(
                    uri=definition.uri,
                    hash="0" * 64,  # Dummy hash for V2 draft compilation
                    scopes=[],  # Default empty scopes
                    risk_level=definition.risk_level,
                )
            )
    return AgentDependencies(tools=tools)


def compile_to_topology(manifest: ManifestV2) -> GraphTopology:
    """Transform the V2 "Linked List" manifest into the V1 "Graph" topology.

    Args:
        manifest: The V2 manifest to compile.

    Returns:
        The compiled V1 GraphTopology.

    Raises:
        ValueError: If validation fails.
    """
    # 1. Strict Validation
    errors = validate_strict(manifest)
    if errors:
        raise ValueError("Manifest validation failed:\n" + "\n".join(errors))

    nodes: List[Node] = []
    edges: List[Union[Edge, ConditionalEdge]] = []

    for step_id, step in manifest.workflow.steps.items():
        visual = _convert_visual_metadata(step.design_metadata)
        node: Node

        # 1. Convert Nodes
        if isinstance(step, AgentStep):
            node = AgentNode(
                id=step_id,
                agent_name=step.agent,
                system_prompt=step.system_prompt,
                config=step.inputs,  # Mapping inputs to config
                visual=visual,
            )
            nodes.append(node)

            # Standard Edge
            if step.next:
                edges.append(Edge(source_node_id=step_id, target_node_id=step.next))

        elif isinstance(step, LogicStep):
            node = LogicNode(
                id=step_id,
                code=step.code,
                visual=visual,
            )
            nodes.append(node)

            # Standard Edge
            if step.next:
                edges.append(Edge(source_node_id=step_id, target_node_id=step.next))

        elif isinstance(step, CouncilStep):
            # Map CouncilStep to a LogicNode (noop) with CouncilConfig
            node = LogicNode(
                id=step_id,
                code="pass  # Council Execution handled by Runtime via council_config",
                council_config=CouncilConfig(
                    strategy=step.strategy,
                    voters=step.voters,
                ),
                visual=visual,
            )
            nodes.append(node)

            # Standard Edge
            if step.next:
                edges.append(Edge(source_node_id=step_id, target_node_id=step.next))

        elif isinstance(step, SwitchStep):
            # Generate logic for the switch
            lines = ["def switch_logic(inputs):"]
            mapping: Dict[str, str] = {}

            for i, (condition, target_id) in enumerate(step.cases.items()):
                key = f"case_{i}"
                mapping[key] = target_id
                lines.append(f"    if {condition}:")
                lines.append(f"        return '{key}'")

            if step.default:
                mapping["default"] = step.default
                lines.append("    return 'default'")
            else:
                lines.append("    raise ValueError('No case matched and no default provided')")

            generated_code = "\n".join(lines)

            node = LogicNode(
                id=step_id,
                code=generated_code,
                visual=visual,
            )
            nodes.append(node)

            # Conditional Edge
            # Using a placeholder identity function because we cannot add new dependencies/libs.
            # We assume the runtime has a way to handle this or the user provides the identity util.
            # Here we use 'coreason.lib.router.identity' as the implied identity function.
            edges.append(
                ConditionalEdge(
                    source_node_id=step_id,
                    router_logic="coreason.lib.router.identity",
                    mapping=mapping,
                )
            )

    return GraphTopology(nodes=nodes, edges=edges)
