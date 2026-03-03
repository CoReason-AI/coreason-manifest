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
from coreason_manifest.core.workflow.flow import GraphFlow, LinearFlow


class ChangeCategory(StrEnum):
    BREAKING = "BREAKING"
    GOVERNANCE = "GOVERNANCE"
    FEATURE = "FEATURE"
    PATCH = "PATCH"


class DiffChange(CoreasonModel):
    path: str
    category: ChangeCategory
    change_type: str = Field(..., description="'add', 'remove', or 'modify'")
    old_value: Any | None = None
    new_value: Any | None = None


class DiffReport(CoreasonModel):
    changes: list[DiffChange]


def _categorize_path(path: str, change_type: str) -> ChangeCategory:
    """Categorize a change based on its path and type."""
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
    """Compare lists using difflib.SequenceMatcher to generate semantic diffs."""
    changes = []

    # Try to extract a stable identifier for complex objects (like nodes/edges) to improve diffing
    def _get_id(item: Any) -> Any:
        if isinstance(item, dict) and "id" in item:
            return item["id"]
        # For edges we might use from_node -> to_node as an identifier
        if isinstance(item, dict) and "from_node" in item and "to_node" in item:
            return f"{item['from_node']}->{item['to_node']}"
        # For simple types just use the value
        if isinstance(item, (str, int, float, bool)) or item is None:
            return item
        # Fallback for complex objects without 'id', hash their string representation
        # It's not perfect but works for simple diffing
        import json

        try:
            return json.dumps(item, sort_keys=True)
        except Exception:
            return str(item)

    old_ids = [_get_id(item) for item in old_list]
    new_ids = [_get_id(item) for item in new_list]

    matcher = difflib.SequenceMatcher(None, old_ids, new_ids)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            # For a replace, we pair up the items and do a deeper diff if they are dicts
            for i, j in zip(range(i1, i2), range(j1, j2), strict=False):
                current_path = f"{path_prefix}[{i}]"
                if isinstance(old_list[i], dict) and isinstance(new_list[j], dict):
                    changes.extend(_compare_dicts(current_path, old_list[i], new_list[j]))
                else:
                    changes.append(
                        DiffChange(
                            path=current_path,
                            category=_categorize_path(current_path, "modify"),
                            change_type="modify",
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
                            category=_categorize_path(current_path, "remove"),
                            change_type="remove",
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
                            category=_categorize_path(current_path, "add"),
                            change_type="add",
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
                        category=_categorize_path(current_path, "remove"),
                        change_type="remove",
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
                        category=_categorize_path(current_path, "add"),
                        change_type="add",
                        old_value=None,
                        new_value=new_list[j],
                    )
                )

    return changes


def _compare_dicts(path_prefix: str, old_dict: dict[str, Any], new_dict: dict[str, Any]) -> list[DiffChange]:
    """Recursively compare two dictionaries."""
    changes = []

    all_keys = set(old_dict.keys()) | set(new_dict.keys())

    for key in all_keys:
        current_path = f"{path_prefix}.{key}" if path_prefix else key

        if key not in old_dict:
            changes.append(
                DiffChange(
                    path=current_path,
                    category=_categorize_path(current_path, "add"),
                    change_type="add",
                    old_value=None,
                    new_value=new_dict[key],
                )
            )
        elif key not in new_dict:
            changes.append(
                DiffChange(
                    path=current_path,
                    category=_categorize_path(current_path, "remove"),
                    change_type="remove",
                    old_value=old_dict[key],
                    new_value=None,
                )
            )
        else:
            old_val = old_dict[key]
            new_val = new_dict[key]

            if isinstance(old_val, dict) and isinstance(new_val, dict):
                changes.extend(_compare_dicts(current_path, old_val, new_val))
            elif isinstance(old_val, list) and isinstance(new_val, list):
                changes.extend(_compare_lists(current_path, old_val, new_val))
            elif old_val != new_val:
                changes.append(
                    DiffChange(
                        path=current_path,
                        category=_categorize_path(current_path, "modify"),
                        change_type="modify",
                        old_value=old_val,
                        new_value=new_val,
                    )
                )

    return changes


def compare_flows(old: GraphFlow | LinearFlow, new: GraphFlow | LinearFlow) -> DiffReport:
    """Compare two flows and return a semantic diff report."""
    old_dict = old.model_dump(exclude_none=True)
    new_dict = new.model_dump(exclude_none=True)

    changes = _compare_dicts("", old_dict, new_dict)

    return DiffReport(changes=changes)
