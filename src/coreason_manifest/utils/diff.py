# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import StrEnum
from typing import Any

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel
from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2


class ChangeCategory(StrEnum):
    """Category of change in the agent definition."""

    BREAKING = "BREAKING"  # API contract violation
    GOVERNANCE = "GOVERNANCE"  # Policy or Safety change
    RESOURCE = "RESOURCE"  # Cost or Rate Limit change
    FEATURE = "FEATURE"  # Adding capability/tool
    PATCH = "PATCH"  # Description, metadata, version bump


class DiffChange(CoReasonBaseModel):
    """A specific change detected in the agent definition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(..., description="Dot-notation path to the field.")
    old_value: Any | None = Field(None, description="The previous value.")
    new_value: Any | None = Field(None, description="The new value.")
    category: ChangeCategory = Field(..., description="The semantic category of the change.")


class DiffReport(CoReasonBaseModel):
    """Report of all semantic changes between two agent definitions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    changes: list[DiffChange] = Field(default_factory=list, description="List of detected changes.")

    @property
    def has_breaking(self) -> bool:
        """Whether any change is BREAKING."""
        return any(c.category == ChangeCategory.BREAKING for c in self.changes)

    @property
    def has_governance_impact(self) -> bool:
        """Whether any change has GOVERNANCE impact."""
        return any(c.category == ChangeCategory.GOVERNANCE for c in self.changes)


def compare_agents(
    old: ManifestV2 | AgentDefinition, new: ManifestV2 | AgentDefinition
) -> DiffReport:
    """
    Compare two agent definitions and return a semantic difference report.

    Args:
        old: The original definition (Manifest or AgentDefinition).
        new: The new definition.

    Returns:
        DiffReport containing categorized changes.
    """
    old_dict = old.model_dump(mode="json", by_alias=True)
    new_dict = new.model_dump(mode="json", by_alias=True)

    changes = []
    _walk_diff("", old_dict, new_dict, changes)

    return DiffReport(changes=changes)


def _walk_diff(
    path: str, old: Any, new: Any, changes: list[DiffChange]
) -> None:
    """Recursively walk and compare two objects."""
    if old == new:
        return

    # Handle type mismatch or None transition
    # This prevents crashing if one is None and the other is a dict/list
    if type(old) is not type(new):
        _add_change(path, old, new, changes)
        return

    if isinstance(old, dict):
        old_keys = set(old.keys())
        new_keys = set(new.keys())

        # Removed keys
        for key in old_keys - new_keys:
            key_path = f"{path}.{key}" if path else key
            _add_change(key_path, old[key], None, changes)

        # Added keys
        for key in new_keys - old_keys:
            key_path = f"{path}.{key}" if path else key
            _add_change(key_path, None, new[key], changes)

        # Common keys
        for key in old_keys & new_keys:
            key_path = f"{path}.{key}" if path else key
            _walk_diff(key_path, old[key], new[key], changes)

    elif isinstance(old, list):
        # Heuristic: List comparison is tricky.
        # We try to match by index for simplicity unless it looks like a list of IDs.
        # But for 'tools' (list of strings), removing an item is important.

        # If lengths differ, we iterate up to max length
        max_len = max(len(old), len(new))
        for i in range(max_len):
            idx_path = f"{path}.{i}"
            if i < len(old) and i < len(new):
                _walk_diff(idx_path, old[i], new[i], changes)
            elif i < len(old):
                # Removed item
                _add_change(idx_path, old[i], None, changes)
            else:
                # Added item
                _add_change(idx_path, None, new[i], changes)
    else:
        # Scalar change
        _add_change(path, old, new, changes)


def _add_change(path: str, old: Any, new: Any, changes: list[DiffChange]) -> None:
    """Determine category and add change to list."""
    category = _categorize_change(path, old, new)
    changes.append(
        DiffChange(
            path=path,
            old_value=old,
            new_value=new,
            category=category,
        )
    )


def _categorize_change(path: str, old: Any, new: Any) -> ChangeCategory:
    """Apply semantic rules to categorize the change."""
    parts = path.split(".")

    # 1. Resource Changes
    if "resources" in parts:
        return ChangeCategory.RESOURCE

    # 2. Governance/Policy Changes
    # 'policy' is the field in ManifestV2
    if "policy" in parts or "governance" in parts:
        return ChangeCategory.GOVERNANCE

    # 3. Interface Changes (Inputs)
    # path examples: interface.inputs.properties.arg_name, interface.inputs.required.0
    if "interface" in parts and "inputs" in parts:
        # Check relative location
        try:
            inputs_idx = parts.index("inputs")
        except ValueError:
            inputs_idx = -1

        if inputs_idx != -1:
            rest = parts[inputs_idx+1:]

            if "properties" in rest:
                # Removing a property is BREAKING
                if new is None:
                    return ChangeCategory.BREAKING
                # Adding a property is FEATURE (unless required, see below)
                if old is None:
                    return ChangeCategory.FEATURE

            if "required" in rest:
                 if old is None and new is not None:
                    return ChangeCategory.BREAKING
                 if new is None:
                    return ChangeCategory.FEATURE

            # If we are strictly at interface.inputs level (or just below without hitting properties/required)
            # e.g. replacing the whole schema
            if not rest:
                # Whole inputs block replaced
                 if new is None:
                     return ChangeCategory.BREAKING
                 # Generally changing the whole input schema is BREAKING unless verified otherwise
                 return ChangeCategory.BREAKING

    # 4. Tools Changes
    if "tools" in parts:
        if new is None:
            return ChangeCategory.BREAKING
        if old is None:
            return ChangeCategory.FEATURE

    # 5. Metadata/Patch
    if "description" in parts or "version" in parts or "metadata" in parts:
        return ChangeCategory.PATCH

    # Default fallback
    return ChangeCategory.PATCH
