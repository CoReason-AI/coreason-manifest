from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict

from coreason_manifest.spec.core.flow import GraphFlow
from coreason_manifest.spec.core.nodes import AgentNode, HumanNode, SwarmNode


class ChangeType(Enum):
    BREAKING = "BREAKING"
    CRITICAL = "CRITICAL"
    BEHAVIORAL = "BEHAVIORAL"
    TOPOLOGICAL = "TOPOLOGICAL"
    COSMETIC = "COSMETIC"


class DiffChange(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: ChangeType
    node_id: str | None  # None if global change
    field: str | None
    old_value: Any
    new_value: Any
    description: str


class ManifestDiff:
    @staticmethod
    def compare(old: GraphFlow, new: GraphFlow) -> list[DiffChange]:
        changes: list[DiffChange] = []

        # 1. Compare Interface (Breaking)
        if old.interface.inputs != new.interface.inputs:
            changes.append(
                DiffChange(
                    type=ChangeType.BREAKING,
                    node_id=None,
                    field="interface.inputs",
                    old_value=str(old.interface.inputs),
                    new_value=str(new.interface.inputs),
                    description="Input schema changed",
                )
            )
        if old.interface.outputs != new.interface.outputs:
            changes.append(
                DiffChange(
                    type=ChangeType.BREAKING,
                    node_id=None,
                    field="interface.outputs",
                    old_value=str(old.interface.outputs),
                    new_value=str(new.interface.outputs),
                    description="Output schema changed",
                )
            )

        # 2. Compare Graph Topology (Topological)
        old_nodes = set(old.graph.nodes.keys())
        new_nodes = set(new.graph.nodes.keys())

        added_nodes = new_nodes - old_nodes
        removed_nodes = old_nodes - new_nodes
        common_nodes = old_nodes & new_nodes

        changes.extend(
            DiffChange(
                type=ChangeType.TOPOLOGICAL,
                node_id=node_id,
                field=None,
                old_value=None,
                new_value="Present",
                description=f"Node '{node_id}' added",
            )
            for node_id in added_nodes
        )
        changes.extend(
            DiffChange(
                type=ChangeType.TOPOLOGICAL,
                node_id=node_id,
                field=None,
                old_value="Present",
                new_value=None,
                description=f"Node '{node_id}' removed",
            )
            for node_id in removed_nodes
        )

        # Compare Edges
        old_edges = {(e.source, e.target, e.condition) for e in old.graph.edges}
        new_edges = {(e.source, e.target, e.condition) for e in new.graph.edges}

        added_edges = new_edges - old_edges
        removed_edges = old_edges - new_edges

        changes.extend(
            DiffChange(
                type=ChangeType.TOPOLOGICAL,
                node_id=None,
                field="edges",
                old_value=None,
                new_value=f"{src}->{tgt}",
                description=f"Edge added: {src} -> {tgt} ({cond})",
            )
            for src, tgt, cond in added_edges
        )
        changes.extend(
            DiffChange(
                type=ChangeType.TOPOLOGICAL,
                node_id=None,
                field="edges",
                old_value=f"{src}->{tgt}",
                new_value=None,
                description=f"Edge removed: {src} -> {tgt} ({cond})",
            )
            for src, tgt, cond in removed_edges
        )

        # 3. Compare Node Details
        for node_id in common_nodes:
            old_node = old.graph.nodes[node_id]
            new_node = new.graph.nodes[node_id]

            # Compare Type
            if old_node.type != new_node.type:
                changes.append(
                    DiffChange(
                        type=ChangeType.TOPOLOGICAL,
                        node_id=node_id,
                        field="type",
                        old_value=old_node.type,
                        new_value=new_node.type,
                        description=f"Node type changed from {old_node.type} to {new_node.type}",
                    )
                )
                continue  # If type changed, comparison of fields might be invalid/messy

            # Compare Metadata (Cosmetic)
            if old_node.metadata != new_node.metadata:
                changes.append(
                    DiffChange(
                        type=ChangeType.COSMETIC,
                        node_id=node_id,
                        field="metadata",
                        old_value=str(old_node.metadata),
                        new_value=str(new_node.metadata),
                        description="Metadata changed",
                    )
                )

            # Presentation (new field)
            old_pres = getattr(old_node, "presentation", None)
            new_pres = getattr(new_node, "presentation", None)
            if old_pres != new_pres:
                changes.append(
                    DiffChange(
                        type=ChangeType.COSMETIC,
                        node_id=node_id,
                        field="presentation",
                        old_value=str(old_pres),
                        new_value=str(new_pres),
                        description="Presentation hints changed",
                    )
                )

            # Compare Specific Node Types

            # AgentNode: Profile (Behavioral), Tools (Critical)
            if isinstance(old_node, AgentNode) and isinstance(new_node, AgentNode):
                # Tools
                old_tools = set(old_node.tools)
                new_tools = set(new_node.tools)
                if old_tools != new_tools:
                    changes.append(
                        DiffChange(
                            type=ChangeType.CRITICAL,
                            node_id=node_id,
                            field="tools",
                            old_value=str(old_tools),
                            new_value=str(new_tools),
                            description=f"Tools changed: {old_tools} -> {new_tools}",
                        )
                    )

                # Profile (Behavioral)
                # If profile is inline (CognitiveProfile object) or ID (str).
                if old_node.profile != new_node.profile:
                    changes.append(
                        DiffChange(
                            type=ChangeType.BEHAVIORAL,
                            node_id=node_id,
                            field="profile",
                            old_value=str(old_node.profile),
                            new_value=str(new_node.profile),
                            description="Cognitive Profile changed",
                        )
                    )

            # HumanNode: Prompt (Behavioral), Timeout (Behavioral?)
            if isinstance(old_node, HumanNode) and isinstance(new_node, HumanNode):
                if old_node.prompt != new_node.prompt:
                    changes.append(
                        DiffChange(
                            type=ChangeType.BEHAVIORAL,
                            node_id=node_id,
                            field="prompt",
                            old_value=old_node.prompt,
                            new_value=new_node.prompt,
                            description="Prompt text changed",
                        )
                    )

                # Interaction mode
                if old_node.interaction_mode != new_node.interaction_mode:
                    changes.append(
                        DiffChange(
                            type=ChangeType.BEHAVIORAL,
                            node_id=node_id,
                            field="interaction_mode",
                            old_value=old_node.interaction_mode,
                            new_value=new_node.interaction_mode,
                            description="Interaction mode changed",
                        )
                    )

            # SwarmNode: Workload (Behavioral?), Worker Profile (Behavioral)
            if (
                isinstance(old_node, SwarmNode)
                and isinstance(new_node, SwarmNode)
                and old_node.worker_profile != new_node.worker_profile
            ):
                changes.append(
                    DiffChange(
                        type=ChangeType.BEHAVIORAL,
                        node_id=node_id,
                        field="worker_profile",
                        old_value=old_node.worker_profile,
                        new_value=new_node.worker_profile,
                        description="Swarm worker profile changed",
                    )
                )

        # 4. Compare Governance (Critical)
        if old.governance != new.governance:
            changes.append(
                DiffChange(
                    type=ChangeType.CRITICAL,
                    node_id=None,
                    field="governance",
                    old_value=str(old.governance),
                    new_value=str(new.governance),
                    description="Governance policy changed",
                )
            )

        return changes
