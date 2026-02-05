# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""I/O module for loading and dumping V2 Manifests."""

from pathlib import Path
from typing import Any

import yaml

from coreason_manifest.spec.v2.definitions import ManifestV2
from coreason_manifest.utils.v2.resolver import ReferenceResolver


def _load_recursive(path: Path, resolver: ReferenceResolver, visited_paths: set[Path]) -> dict[str, Any]:
    """
    Recursively load YAML data, resolving $ref in definitions.

    Handles cycle detection to prevent infinite recursion and uses the
    ReferenceResolver to ensure secure path resolution.
    """
    if path in visited_paths:
        raise RecursionError(f"Circular dependency detected: {path}")

    visited_paths.add(path)

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Expected a dictionary in {path}, got {type(data).__name__}")

    # Resolve references in definitions
    definitions = data.get("definitions", {})
    if definitions:
        for key, value in definitions.items():
            if isinstance(value, dict) and "$ref" in value:
                ref_path_str = value["$ref"]
                # Resolve the path
                abs_path = resolver.resolve(path, ref_path_str)

                # Recursively load
                loaded_obj = _load_recursive(abs_path, resolver, visited_paths)

                # Merge Strategy:
                # Replace the $ref dict with the loaded data.
                definitions[key] = loaded_obj

    visited_paths.remove(path)
    return data


def load_from_yaml(
    path: str | Path,
    root_dir: str | Path | None = None,
    recursive: bool = True,
) -> ManifestV2:
    """Load a V2 manifest from a YAML file.

    Args:
        path: Path to the YAML file.
        root_dir: The allowed root directory for references. Defaults to path's parent.
        recursive: Whether to resolve $ref recursively.

    Returns:
        The validated ManifestV2 object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValidationError: If the manifest is invalid.
        yaml.YAMLError: If the YAML is invalid.
        RecursionError: If a cyclic dependency is detected.
        ValueError: If a security violation occurs or YAML is invalid.
    """
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    if root_dir is None:
        root_dir = p.parent

    if recursive:
        resolver = ReferenceResolver(root_dir)
        visited_paths: set[Path] = set()
        data = _load_recursive(p, resolver, visited_paths)
    else:
        with p.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

    return ManifestV2.model_validate(data)


def dump_to_yaml(manifest: ManifestV2) -> str:
    """Dump a V2 manifest to a YAML string.

    Ensures that apiVersion, kind, and metadata appear at the top.

    Args:
        manifest: The ManifestV2 object to dump.

    Returns:
        The YAML string representation.
    """
    # Serialize to dict, using aliases (e.g., x-design) and excluding None
    data = manifest.model_dump(by_alias=True, exclude_none=True)

    # Reorder keys to ensure human readability
    # Priority keys: apiVersion, kind, metadata
    ordered_keys = ["apiVersion", "kind", "metadata"]
    ordered_data = {}

    # 1. Add priority keys
    for key in ordered_keys:
        if key in data:
            ordered_data[key] = data.pop(key)

    # 2. Add remaining keys
    ordered_data.update(data)

    # Dump using PyYAML, preserving key order (sort_keys=False)
    # allow_unicode=True ensures proper string representation
    return yaml.dump(ordered_data, sort_keys=False, allow_unicode=True)
