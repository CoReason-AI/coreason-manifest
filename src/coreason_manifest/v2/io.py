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
from typing import Union

import yaml

from coreason_manifest.v2.spec.definitions import ManifestV2


def load_from_yaml(path: Union[str, Path]) -> ManifestV2:
    """Load a V2 manifest from a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        The validated ManifestV2 object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValidationError: If the manifest is invalid.
        yaml.YAMLError: If the YAML is invalid.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")

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
