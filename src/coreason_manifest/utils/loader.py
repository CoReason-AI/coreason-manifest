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

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.utils.v2.io import ManifestIO


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
        SecurityViolation: If path traversal or unsafe permissions are detected.
    """
    file_path = Path(path).resolve()
    root_dir = file_path.parent

    # Initialize secure loader confined to the file's directory
    loader = ManifestIO(root_dir=root_dir)

    try:
        data = loader.load(file_path.name)
    except Exception as e:
        # Re-raise known exceptions or wrap them
        raise e

    if not isinstance(data, dict):
        raise ValueError("Manifest content must be a dictionary/object.")

    kind = data.get("kind")
    if kind == "LinearFlow":
        return LinearFlow.model_validate(data)
    if kind == "GraphFlow":
        return GraphFlow.model_validate(data)
    raise ValueError(f"Unknown or missing manifest kind: {kind}. Expected 'LinearFlow' or 'GraphFlow'.")
