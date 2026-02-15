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

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.utils.io import ManifestIO, SecurityViolationError

__all__ = ["load_flow_from_file", "SecurityViolationError"]


def load_flow_from_file(path: str, root_dir: Path | None = None) -> LinearFlow | GraphFlow:
    """
    Load a flow manifest from a YAML or JSON file.

    Args:
        path: Path to the manifest file.
        root_dir: Optional root directory for path confinement. Defaults to file's parent.

    Returns:
        LinearFlow | GraphFlow: The parsed flow object.

    Raises:
        ValueError: If the file content is invalid or the kind is unknown.
        FileNotFoundError: If the file does not exist.
        SecurityViolationError: If path traversal or unsafe permissions are detected.
    """
    file_path = Path(path).resolve()
    jail_root = root_dir or file_path.parent

    # Initialize secure loader confined to the file's directory
    loader = ManifestIO(root_dir=jail_root)

    # Pass relative path from jail root to ensure loader can resolve it correctly
    try:
        rel_path = file_path.relative_to(jail_root)
    except ValueError:
        # If file is not inside root_dir, let ManifestIO raise the security error
        # or handle it here. ManifestIO handles absolute paths too if allow_external is False.
        # But for clarity, we pass the relative path if possible, or just the name if same dir.
        rel_path = file_path.name

    data = loader.load(str(rel_path))

    kind = data.get("kind")
    if kind == "LinearFlow":
        return LinearFlow.model_validate(data)
    if kind == "GraphFlow":
        return GraphFlow.model_validate(data)
    raise ValueError(f"Unknown or missing manifest kind: {kind}. Expected 'LinearFlow' or 'GraphFlow'.")
