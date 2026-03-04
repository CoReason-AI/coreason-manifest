# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import difflib
from enum import StrEnum
from typing import Any

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.workflow.flow import WorkflowEnvelope


class ChangeCategory(StrEnum):
    BREAKING = "BREAKING"
    GOVERNANCE = "GOVERNANCE"
    FEATURE = "FEATURE"
    PATCH = "PATCH"


class ChangeType(StrEnum):
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"


class DiffChange(CoreasonModel):
    path: str
    category: ChangeCategory
    change_type: ChangeType = Field(..., description="'add', 'remove', or 'modify'")
    old_value: Any | None = None
    new_value: Any | None = None


class DiffReport(CoreasonModel):
    changes: list[DiffChange]


def _categorize_path(path: str, change_type: str) -> ChangeCategory:
    """Analyze the nested string path and operation semantic to determine a standardized impact categorization.

    Provides a heuristic layer that accurately translates technical state
    mutations into domain-specific execution policies (e.g. governing node insertions
    vs security rules).

    Complexity:
        Time: $O(1)$, strictly constrained string length checks resolving instantaneously.
        Space: $O(1)$, constant evaluation frames per path resolution.

    Args:
        path: The hierarchical JSON-Patch style pointer indicating the mutation target.
        change_type: The semantic operation ('add', 'modify', 'remove') applied to the state object.

    Returns:
        The enumerated policy categorization mapped to the path mutation.
    """
    if (
        "governance" in path
        or "circuit_breaker" in path
        or "operational_policy" in path
        or "resilience" in path
        or "escalation_rules" in path
    ):
        return ChangeCategory.GOVERNANCE

    if "tools" in path:
        return ChangeCategory.FEATURE

    if "description" in path or "name" in path or "label" in path:
        return ChangeCategory.PATCH

    if change_type == "remove" and ("nodes" in path or "edges" in path or "steps" in path):
        return ChangeCategory.BREAKING

    if "type" in path or "id" in path or "entry_point" in path:
        return ChangeCategory.BREAKING

    # Default logic for generic additions/modifications
    if change_type == "add":
        return ChangeCategory.FEATURE

    return ChangeCategory.PATCH


def _compare_lists(path_prefix: str, old_list: list[Any], new_list: list[Any]) -> list[DiffChange]:
    """Execute a semantic alignment sequence match on linear state boundaries.

    Heuristically employs a dynamic programming subsequence evaluation against
    stable object identifiers. This guarantees optimal, semantic context retention
    rather than brittle index-based differences when flow structures evolve.

    Complexity:
        Time: Expected $O(N)$ with reliable identifiers, upper-bound $O(N \cdot M)$ evaluating disparate states.
        Space: $O(N + M)$, dynamically allocating normalized state tracking schemas for both the current and pending list.

    Args:
        path_prefix: The cumulative path prefix resolving to the currently evaluated list.
        old_list: The preceding linear array context requiring temporal comparison.
        new_list: The superseding linear array dictating modern structural constraints.

    Returns:
        The sequential stream of delta objects identifying all localized additions, deletions, or structural modifications.
    """  # noqa: E501
    changes = []

    # Try to extract a stable identifier for complex objects (like nodes/edges) to improve diffing
    def _get_id(item: Any) -> Any:
        """Resolve a consistent hashing or identity reference for semantic state diffing.

        Forces disparate python typings or unsorted dictionaries into normalized, predictable identifiers.

        Complexity:
            Time: Expected $O(1)$ dictionary lookup; $O(S)$ fallback JSON serialization, where $S$ is size of structure.
            Space: $O(S)$ dynamically constrained buffer on complex type serialization.

        Args:
            item: The localized node, structural context, or primitive targeted for identifier extraction.
        """
        if isinstance(item, dict) and "id" in item:
            return item["id"]
        if hasattr(item, "id"):
            return item.id

        # For edges we might use from_node -> to_node as an identifier
        if isinstance(item, dict) and "from_node" in item and "to_node" in item:
            return f"{item['from_node']}->{item['to_node']}"
        if hasattr(item, "from_node") and hasattr(item, "to_node"):
            return f"{item.from_node}->{item.to_node}"

        # For simple types just use the value
        if isinstance(item, (str, int, float, bool)) or item is None:
            return item

        # ENFORCED STRICT HASHING
        if hasattr(item, "canonical_id"):
            try:
                return item.canonical_id()
            except (TypeError, ValueError):
                pass

        raise ValueError(
            f"Object of type {type(item).__name__} must implement a .canonical_id() method for strict hashing."
        )

    old_ids = [_get_id(item) for item in old_list]
    new_ids = [_get_id(item) for item in new_list]

    matcher = difflib.SequenceMatcher(None, old_ids, new_ids)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            # For a replace, we pair up the items and do a deeper diff if they are dicts or objects
            for i, j in zip(range(i1, i2), range(j1, j2), strict=False):
                current_path = f"{path_prefix}[{i}]"
                is_old_complex = isinstance(old_list[i], dict) or hasattr(old_list[i], "model_fields")
                is_new_complex = isinstance(new_list[j], dict) or hasattr(new_list[j], "model_fields")

                if is_old_complex and is_new_complex:
                    changes.extend(_compare_objects(current_path, old_list[i], new_list[j]))
                else:
                    changes.append(
                        DiffChange(
                            path=current_path,
                            category=_categorize_path(current_path, ChangeType.MODIFY),
                            change_type=ChangeType.MODIFY,
                            old_value=old_list[i],
                            new_value=new_list[j],
                        )
                    )
            # If lengths differ, treat the rest as inserts or deletes
            if i2 - i1 > j2 - j1:
                for i in range(i1 + (j2 - j1), i2):
                    current_path = f"{path_prefix}[{i}]"
                    changes.append(
                        DiffChange(
                            path=current_path,
                            category=_categorize_path(current_path, ChangeType.REMOVE),
                            change_type=ChangeType.REMOVE,
                            old_value=old_list[i],
                            new_value=None,
                        )
                    )
            elif j2 - j1 > i2 - i1:
                for j in range(j1 + (i2 - i1), j2):
                    current_path = f"{path_prefix}[{j}]"
                    changes.append(
                        DiffChange(
                            path=current_path,
                            category=_categorize_path(current_path, ChangeType.ADD),
                            change_type=ChangeType.ADD,
                            old_value=None,
                            new_value=new_list[j],
                        )
                    )
        elif tag == "delete":
            for i in range(i1, i2):
                current_path = f"{path_prefix}[{i}]"
                changes.append(
                    DiffChange(
                        path=current_path,
                        category=_categorize_path(current_path, ChangeType.REMOVE),
                        change_type=ChangeType.REMOVE,
                        old_value=old_list[i],
                        new_value=None,
                    )
                )
        elif tag == "insert":
            for j in range(j1, j2):
                current_path = f"{path_prefix}[{j}]"
                changes.append(
                    DiffChange(
                        path=current_path,
                        category=_categorize_path(current_path, ChangeType.ADD),
                        change_type=ChangeType.ADD,
                        old_value=None,
                        new_value=new_list[j],
                    )
                )

    return changes


def _compare_objects(path_prefix: str, old_obj: Any, new_obj: Any) -> list[DiffChange]:
    """Recursively dissect dynamic structural maps and objects to extract highly precise mutation contexts.

    Iterates over key unions iteratively unpacking nested maps and primitive structures
    into explicit path pointers. This strictly enables structural versioning without schema constraints.

    Complexity:
        Time: $O(K)$, bounded heavily by the unified cardinality of distinct dictionary keys across states.
        Space: $O(D)$, strictly matching the max nesting depth across execution call frames.

    Args:
        path_prefix: The semantic structural prefix pinpointing this localized state path.
        old_obj: The initial representation of semantic mappings prior to the differential check.
        new_obj: The targeted final state mappings indicating current execution policy goals.

    Returns:
        An inclusive list aggregating the distinct, recursive patches defining the dictionary state divergence.
    """
    changes = []

    def get_keys(obj: Any) -> set[str]:
        if isinstance(obj, dict):
            return set(obj.keys())
        if hasattr(obj, "model_fields"):
            keys = set()
            for key in obj.model_fields:
                val = getattr(obj, key)
                if val is not None:
                    keys.add(key)
            return keys
        return set()

    def get_val(obj: Any, key: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    old_keys = get_keys(old_obj)
    new_keys = get_keys(new_obj)
    all_keys = old_keys | new_keys

    for key in all_keys:
        current_path = f"{path_prefix}.{key}" if path_prefix else key

        old_has_key = key in old_keys
        new_has_key = key in new_keys

        if not old_has_key and new_has_key:
            changes.append(
                DiffChange(
                    path=current_path,
                    category=_categorize_path(current_path, ChangeType.ADD),
                    change_type=ChangeType.ADD,
                    old_value=None,
                    new_value=get_val(new_obj, key),
                )
            )
        elif old_has_key and not new_has_key:
            changes.append(
                DiffChange(
                    path=current_path,
                    category=_categorize_path(current_path, ChangeType.REMOVE),
                    change_type=ChangeType.REMOVE,
                    old_value=get_val(old_obj, key),
                    new_value=None,
                )
            )
        else:
            old_val = get_val(old_obj, key)
            new_val = get_val(new_obj, key)

            is_old_complex = isinstance(old_val, dict) or hasattr(old_val, "model_fields")
            is_new_complex = isinstance(new_val, dict) or hasattr(new_val, "model_fields")

            if is_old_complex and is_new_complex:
                changes.extend(_compare_objects(current_path, old_val, new_val))
            elif isinstance(old_val, list) and isinstance(new_val, list):
                changes.extend(_compare_lists(current_path, old_val, new_val))
            elif old_val != new_val:
                changes.append(
                    DiffChange(
                        path=current_path,
                        category=_categorize_path(current_path, ChangeType.MODIFY),
                        change_type=ChangeType.MODIFY,
                        old_value=old_val,
                        new_value=new_val,
                    )
                )

    return changes


def compare_flows(old: WorkflowEnvelope, new: WorkflowEnvelope) -> DiffReport:
    """Analyze and quantify architectural variances traversing entire workflow definitions.

    Translates rigorous programmatic object state into raw dictionary representations
    capable of extensive, precise schema dissection to fuel automated semantic reporting models.

    Complexity:
        Time: Heavily bounded $O(V+E)$ directly reflective of unified node topological state parsing and serialization limits.
        Space: $O(V+E)$, directly serializing both isolated architectural object graphs simultaneously into application memory.

    Args:
        old: The foundational execution structure serving as the immutable difference target.
        new: The volatile target workflow representing incoming structural changes.

    Returns:
        The consolidated report modeling all localized mutations natively organized and categorized for downstream consumption.
    """  # noqa: E501
    changes = _compare_objects("", old, new)

    return DiffReport(changes=changes)
