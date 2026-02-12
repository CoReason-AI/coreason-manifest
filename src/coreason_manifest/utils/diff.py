from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict

from coreason_manifest.spec.core.flow import GraphFlow


class ChangeCategory(str, Enum):
    BREAKING = "BREAKING"  # Contract violation
    GOVERNANCE = "GOVERNANCE"  # Policy/Safety
    RESOURCE = "RESOURCE"  # Cost/Reliability
    FEATURE = "FEATURE"  # Additive
    PATCH = "PATCH"  # Metadata/Internal


class DiffChange(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    path: str
    old: Any
    new: Any
    category: ChangeCategory


def compare_manifests(old: GraphFlow, new: GraphFlow) -> list[DiffChange]:
    changes: list[DiffChange] = []

    # 1. Interface
    if old.interface != new.interface:
        changes.append(
            DiffChange(
                path="interface", old=old.interface, new=new.interface, category=ChangeCategory.BREAKING
            )
        )

    # 2. Tool Packs
    old_packs = old.definitions.tool_packs if old.definitions else {}
    new_packs = new.definitions.tool_packs if new.definitions else {}
    _diff_dicts(old_packs, new_packs, "definitions.tool_packs", changes, item_category=ChangeCategory.BREAKING)

    # 3. Governance
    if old.governance != new.governance:
        changes.append(
            DiffChange(
                path="governance",
                old=old.governance,
                new=new.governance,
                category=ChangeCategory.GOVERNANCE,
            )
        )

    # 4. Graph Nodes
    old_nodes = old.graph.nodes
    new_nodes = new.graph.nodes

    # Feature/Breaking for add/remove
    changes.extend(
        [
            DiffChange(
                path=f"graph.nodes.{nid}", old=None, new=new_nodes[nid], category=ChangeCategory.FEATURE
            )
            for nid in set(new_nodes) - set(old_nodes)
        ]
    )
    changes.extend(
        [
            DiffChange(
                path=f"graph.nodes.{nid}",
                old=old_nodes[nid],
                new=None,
                category=ChangeCategory.BREAKING,
            )
            for nid in set(old_nodes) - set(new_nodes)
        ]
    )

    # Deep Compare Intersection
    for nid in set(old_nodes) & set(new_nodes):
        _deep_node_compare(f"graph.nodes.{nid}", old_nodes[nid], new_nodes[nid], changes)

    # 5. Profiles
    old_profs = old.definitions.profiles if old.definitions else {}
    new_profs = new.definitions.profiles if new.definitions else {}

    # Profile changes are generally PATCH unless reasoning model changes (RESOURCE)
    changes.extend(
        [
            DiffChange(
                path=f"definitions.profiles.{pid}",
                old=None,
                new=new_profs[pid],
                category=ChangeCategory.FEATURE,
            )
            for pid in set(new_profs) - set(old_profs)
        ]
    )
    changes.extend(
        [
            DiffChange(
                path=f"definitions.profiles.{pid}",
                old=old_profs[pid],
                new=None,
                category=ChangeCategory.BREAKING,
            )
            for pid in set(old_profs) - set(new_profs)
        ]
    )

    for pid in set(old_profs) & set(new_profs):
        old_p, new_p = old_profs[pid], new_profs[pid]
        if old_p != new_p:
            # Check specifically for Model/Cost changes
            old_m = getattr(old_p.reasoning, "model", None) if old_p.reasoning else None
            new_m = getattr(new_p.reasoning, "model", None) if new_p.reasoning else None
            if old_m != new_m:
                changes.append(
                    DiffChange(
                        path=f"definitions.profiles.{pid}.reasoning.model",
                        old=old_m,
                        new=new_m,
                        category=ChangeCategory.RESOURCE,
                    )
                )
            else:
                changes.append(
                    DiffChange(
                        path=f"definitions.profiles.{pid}",
                        old=old_p,
                        new=new_p,
                        category=ChangeCategory.PATCH,
                    )
                )

    return changes


def _diff_dicts(
    old: dict[str, Any],
    new: dict[str, Any],
    path_prefix: str,
    changes: list[DiffChange],
    item_category: ChangeCategory,
) -> None:
    """Generic dict diff helper."""
    changes.extend(
        [
            DiffChange(path=f"{path_prefix}.{k}", old=None, new=new[k], category=ChangeCategory.FEATURE)
            for k in set(new) - set(old)
        ]
    )
    changes.extend(
        [
            DiffChange(path=f"{path_prefix}.{k}", old=old[k], new=None, category=item_category)
            for k in set(old) - set(new)
        ]
    )
    changes.extend(
        [
            DiffChange(path=f"{path_prefix}.{k}", old=old[k], new=new[k], category=item_category)
            for k in set(old) & set(new)
            if old[k] != new[k]
        ]
    )


def _deep_node_compare(path: str, old_node: Any, new_node: Any, changes: list[DiffChange]) -> None:
    """Detailed node comparison."""
    # 1. Polymorphism Check
    if old_node.type != new_node.type:
        changes.append(
            DiffChange(
                path=f"{path}.type",
                old=old_node.type,
                new=new_node.type,
                category=ChangeCategory.BREAKING,
            )
        )
        return

    # 2. Supervision (Reliability)
    if old_node.supervision != new_node.supervision:
        changes.append(
            DiffChange(
                path=f"{path}.supervision",
                old=old_node.supervision,
                new=new_node.supervision,
                category=ChangeCategory.RESOURCE,
            )
        )

    # 3. Type-Specific Logic (The SOTA Upgrade)
    if old_node.type == "agent":
        _diff_agent_node(path, old_node, new_node, changes)
    elif old_node.type == "inspector" and old_node.criteria != new_node.criteria:
        # Changing criteria is strict governance - Fixed SIM102 (combined if)
        changes.append(
            DiffChange(
                path=f"{path}.criteria",
                old=old_node.criteria,
                new=new_node.criteria,
                category=ChangeCategory.GOVERNANCE,
            )
        )

    # 4. Fallback for unhandled fields
    # Fixed SIM102 (combined if)
    if old_node != new_node and not any(c.path.startswith(path) for c in changes):
        changes.append(DiffChange(path=path, old=old_node, new=new_node, category=ChangeCategory.PATCH))


def _diff_agent_node(path: str, old: Any, new: Any, changes: list[DiffChange]) -> None:
    """Specialized logic for Agent Nodes."""
    # Tools: Removal = BREAKING, Addition = FEATURE
    old_tools = set(old.tools)
    new_tools = set(new.tools)

    removed = old_tools - new_tools
    added = new_tools - old_tools

    if removed:
        changes.append(
            DiffChange(path=f"{path}.tools", old=list(removed), new=None, category=ChangeCategory.BREAKING)
        )
    if added:
        changes.append(
            DiffChange(path=f"{path}.tools", old=None, new=list(added), category=ChangeCategory.FEATURE)
        )

    # Profile: Inline definition change could be RESOURCE (model) or GOVERNANCE (prompt)
    if old.profile != new.profile:
        # If it's a string ref change, it's a PATCH (pointers changed)
        # For safety, changing the profile reference is often significant.
        changes.append(
            DiffChange(path=f"{path}.profile", old=old.profile, new=new.profile, category=ChangeCategory.PATCH)
        )
