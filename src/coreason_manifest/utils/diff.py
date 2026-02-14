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


def _deep_diff(path: str, obj1: Any, obj2: Any, change_type: ChangeType, node_id: str | None) -> list[DiffChange]:
    changes: list[DiffChange] = []

    if obj1 == obj2:
        return changes

    if isinstance(obj1, dict) and isinstance(obj2, dict):
        all_keys = set(obj1.keys()) | set(obj2.keys())
        for key in all_keys:
            new_path = f"{path}.{key}" if path else key
            if key not in obj1:
                changes.append(
                    DiffChange(
                        type=change_type,
                        node_id=node_id,
                        field=new_path,
                        old_value=None,
                        new_value=obj2[key],
                        description=f"Field '{new_path}' added",
                    )
                )
            elif key not in obj2:
                changes.append(
                    DiffChange(
                        type=change_type,
                        node_id=node_id,
                        field=new_path,
                        old_value=obj1[key],
                        new_value=None,
                        description=f"Field '{new_path}' removed",
                    )
                )
            else:
                changes.extend(_deep_diff(new_path, obj1[key], obj2[key], change_type, node_id))
    else:
        # For lists or primitives that differ
        changes.append(
            DiffChange(
                type=change_type,
                node_id=node_id,
                field=path,
                old_value=str(obj1),
                new_value=str(obj2),
                description=f"Field '{path}' changed",
            )
        )

    return changes


class ManifestDiff:
    @staticmethod
    def compare(old: GraphFlow, new: GraphFlow) -> list[DiffChange]:
        changes: list[DiffChange] = []

        # 1. Compare Interface (Breaking)
        if old.interface.inputs != new.interface.inputs:
            changes.extend(
                _deep_diff(
                    "interface.inputs",
                    old.interface.inputs.model_dump(),
                    new.interface.inputs.model_dump(),
                    ChangeType.BREAKING,
                    None,
                )
            )
        if old.interface.outputs != new.interface.outputs:
            changes.extend(
                _deep_diff(
                    "interface.outputs",
                    old.interface.outputs.model_dump(),
                    new.interface.outputs.model_dump(),
                    ChangeType.BREAKING,
                    None,
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
                changes.extend(
                    _deep_diff("metadata", old_node.metadata, new_node.metadata, ChangeType.COSMETIC, node_id)
                )

            # Presentation (new field)
            old_pres = getattr(old_node, "presentation", None)
            new_pres = getattr(new_node, "presentation", None)
            if old_pres != new_pres:
                val1 = old_pres.model_dump(exclude_none=True) if old_pres else {}
                val2 = new_pres.model_dump(exclude_none=True) if new_pres else {}
                changes.extend(_deep_diff("presentation", val1, val2, ChangeType.COSMETIC, node_id))

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
                if old_node.profile != new_node.profile:
                    if isinstance(old_node.profile, str) or isinstance(new_node.profile, str):
                        changes.append(
                            DiffChange(
                                type=ChangeType.BEHAVIORAL,
                                node_id=node_id,
                                field="profile",
                                old_value=str(old_node.profile),
                                new_value=str(new_node.profile),
                                description="Cognitive Profile changed (ID reference)",
                            )
                        )
                    else:
                        changes.extend(
                            _deep_diff(
                                "profile",
                                old_node.profile.model_dump(exclude_none=True),
                                new_node.profile.model_dump(exclude_none=True),
                                ChangeType.BEHAVIORAL,
                                node_id,
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
            val1 = old.governance.model_dump(exclude_none=True) if old.governance else {}
            val2 = new.governance.model_dump(exclude_none=True) if new.governance else {}
            changes.extend(_deep_diff("governance", val1, val2, ChangeType.CRITICAL, None))

        return changes
