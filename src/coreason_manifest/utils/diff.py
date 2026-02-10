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

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import ManifestBaseModel
from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2


class ChangeCategory(StrEnum):
    """Category of change in the agent definition."""

    BREAKING = "BREAKING"  # API contract violation
    GOVERNANCE = "GOVERNANCE"  # Policy or Safety change
    RESOURCE = "RESOURCE"  # Cost or Rate Limit change
    FEATURE = "FEATURE"  # Adding capability/tool
    PATCH = "PATCH"  # Description, metadata, version bump


class DiffChange(ManifestBaseModel):
    """A specific change detected in the agent definition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(..., description="Dot-notation path to the field.")
    old_value: Any | None = Field(None, description="The previous value.")
    new_value: Any | None = Field(None, description="The new value.")
    category: ChangeCategory = Field(..., description="The semantic category of the change.")


class DiffReport(ManifestBaseModel):
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


def compare_agents(old: ManifestV2 | AgentDefinition, new: ManifestV2 | AgentDefinition) -> DiffReport:
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

    changes: list[DiffChange] = []
    _walk_diff("", old_dict, new_dict, changes)

    return DiffReport(changes=changes)


def _make_hashable(value: Any) -> Any:
    """Convert a value to a hashable representation for diffing."""
    if isinstance(value, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_make_hashable(v) for v in value)
    return value


def _walk_diff(path: str, old: Any, new: Any, changes: list[DiffChange]) -> None:
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
        # Use difflib to find optimal matching of items (LCS)
        # This handles insertions/deletions much better than index-based comparison
        # and avoids expensive recursive comparisons for shifted items.

        try:
            old_h = [_make_hashable(x) for x in old]
            new_h = [_make_hashable(x) for x in new]
            matcher = difflib.SequenceMatcher(None, old_h, new_h, autojunk=False)

            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == "equal":
                    continue

                if tag == "replace":
                    # Items changed in place. We iterate over both ranges.
                    # Since lengths might differ, we map up to the shorter length,
                    # and treat the rest as insert/delete.
                    len_old_chunk = i2 - i1
                    len_new_chunk = j2 - j1
                    common_len = min(len_old_chunk, len_new_chunk)

                    for k in range(common_len):
                        # Use new index for path to be consistent with 'where is it now'
                        idx_new = j1 + k
                        _walk_diff(f"{path}.{idx_new}", old[i1 + k], new[j1 + k], changes)

                    # Handle remaining items
                    if len_old_chunk > len_new_chunk:
                        # Deletions (excess old items)
                        for k in range(common_len, len_old_chunk):
                            idx_old = i1 + k
                            _add_change(f"{path}.{idx_old}", old[idx_old], None, changes)
                    elif len_new_chunk > len_old_chunk:
                        # Insertions (excess new items)
                        for k in range(common_len, len_new_chunk):
                            idx_new = j1 + k
                            _add_change(f"{path}.{idx_new}", None, new[idx_new], changes)

                elif tag == "delete":
                    for i in range(i1, i2):
                        # Use old index for deletion path
                        _add_change(f"{path}.{i}", old[i], None, changes)

                elif tag == "insert":
                    for j in range(j1, j2):
                        # Use new index for insertion path
                        _add_change(f"{path}.{j}", None, new[j], changes)

        except Exception:
            # Fallback to simple index-based comparison if difflib fails
            # This ensures robustness against unforeseen issues with _make_hashable
            max_len = max(len(old), len(new))
            for i in range(max_len):
                idx_path = f"{path}.{i}"
                if i < len(old) and i < len(new):
                    _walk_diff(idx_path, old[i], new[i], changes)
                elif i < len(old):
                    _add_change(idx_path, old[i], None, changes)
                else:
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
        inputs_idx = parts.index("inputs")
        rest = parts[inputs_idx + 1 :]

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
