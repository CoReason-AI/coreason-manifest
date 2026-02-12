from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict

from coreason_manifest.spec.core.flow import GraphFlow


class ChangeCategory(str, Enum):
    BREAKING = "BREAKING"
    GOVERNANCE = "GOVERNANCE"
    RESOURCE = "RESOURCE"
    FEATURE = "FEATURE"
    PATCH = "PATCH"

class DiffChange(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    path: str
    old: Any
    new: Any
    category: ChangeCategory

def compare_manifests(old: GraphFlow, new: GraphFlow) -> list[DiffChange]:
    changes: list[DiffChange] = []

    # 1. Compare Metadata (PATCH)
    if old.metadata != new.metadata:
        changes.append(DiffChange(
            path="metadata",
            old=old.metadata,
            new=new.metadata,
            category=ChangeCategory.PATCH
        ))

    # 2. Compare Governance (GOVERNANCE)
    if old.governance != new.governance:
        changes.append(DiffChange(
            path="governance",
            old=old.governance,
            new=new.governance,
            category=ChangeCategory.GOVERNANCE
        ))

    # 3. Compare Graph Nodes
    old_nodes = old.graph.nodes
    new_nodes = new.graph.nodes

    # Added Nodes (FEATURE)
    changes.extend([
        DiffChange(
            path=f"graph.nodes.{node_id}",
            old=None,
            new=new_nodes[node_id],
            category=ChangeCategory.FEATURE
        )
        for node_id in set(new_nodes) - set(old_nodes)
    ])

    # Removed Nodes (BREAKING)
    changes.extend([
        DiffChange(
            path=f"graph.nodes.{node_id}",
            old=old_nodes[node_id],
            new=None,
            category=ChangeCategory.BREAKING
        )
        for node_id in set(old_nodes) - set(new_nodes)
    ])

    # Changed Nodes
    for node_id in set(old_nodes) & set(new_nodes):
        old_node = old_nodes[node_id]
        new_node = new_nodes[node_id]

        if old_node != new_node:
            # Polymorphism Check
            if old_node.type != new_node.type:
                changes.append(DiffChange(
                    path=f"graph.nodes.{node_id}",
                    old=old_node,
                    new=new_node,
                    category=ChangeCategory.BREAKING
                ))
            else:
                # Content Change
                changes.append(DiffChange(
                    path=f"graph.nodes.{node_id}",
                    old=old_node,
                    new=new_node,
                    category=ChangeCategory.PATCH
                ))

    # 4. Compare definitions.profiles
    old_profiles = old.definitions.profiles if old.definitions else {}
    new_profiles = new.definitions.profiles if new.definitions else {}

    # Check for Resource changes (Model changes) in shared profiles
    for profile_id in set(old_profiles) & set(new_profiles):
        old_p = old_profiles[profile_id]
        new_p = new_profiles[profile_id]

        if old_p != new_p:
            # Check reasoning config model change
            old_model = getattr(old_p.reasoning, 'model', None) if old_p.reasoning else None
            new_model = getattr(new_p.reasoning, 'model', None) if new_p.reasoning else None

            if old_model != new_model:
                changes.append(DiffChange(
                    path=f"definitions.profiles.{profile_id}.reasoning.model",
                    old=old_model,
                    new=new_model,
                    category=ChangeCategory.RESOURCE
                ))

            # If model didn't change (or was None), report generic PATCH for profile.
            else:
                changes.append(DiffChange(
                    path=f"definitions.profiles.{profile_id}",
                    old=old_p,
                    new=new_p,
                    category=ChangeCategory.PATCH
                ))

    # Added/Removed profiles
    changes.extend([
        DiffChange(
            path=f"definitions.profiles.{profile_id}",
            old=None,
            new=new_profiles[profile_id],
            category=ChangeCategory.FEATURE
        )
        for profile_id in set(new_profiles) - set(old_profiles)
    ])

    changes.extend([
        DiffChange(
            path=f"definitions.profiles.{profile_id}",
            old=old_profiles[profile_id],
            new=None,
            category=ChangeCategory.BREAKING
        )
        for profile_id in set(old_profiles) - set(new_profiles)
    ])

    return changes
