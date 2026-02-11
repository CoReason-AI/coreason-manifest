# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from pathlib import Path
from typing import Any

import yaml

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow


def load_flow_from_file(path: str) -> LinearFlow | GraphFlow:
    """
    Load a flow manifest from a YAML or JSON file.

    Args:
        path: Path to the manifest file.

    Returns:
        LinearFlow | GraphFlow: The parsed flow object.

    Raises:
        ValueError: If the file content is invalid or the kind is unknown.
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()

    try:
        # yaml.safe_load parses both YAML and JSON
        data: dict[str, Any] = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse manifest file: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Manifest content must be a dictionary/object.")

    kind = data.get("kind")
    if kind == "LinearFlow":
        return LinearFlow.model_validate(data)
    if kind == "GraphFlow":
        return GraphFlow.model_validate(data)
    raise ValueError(f"Unknown or missing manifest kind: {kind}. Expected 'LinearFlow' or 'GraphFlow'.")
