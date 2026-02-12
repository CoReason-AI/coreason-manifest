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


class SecurityError(Exception):
    """Raised when a security boundary is violated."""
    pass


class CitadelLoader:
    """
    Secure Recursive Loader ("The Citadel").
    Enforces strict security boundaries for file loading and $ref resolution.
    """

    def __init__(self, root_path: Path):
        """
        Initialize the loader with a root jail path.
        All loaded files must reside within this path.
        """
        self.root_path = root_path.resolve()

    def _resolve_path(self, base_dir: Path, ref_path: str) -> Path:
        """
        Resolve a reference path relative to base_dir and ensure it is within the jail.
        """
        # Resolve path relative to the current file's directory
        target = (base_dir / ref_path).resolve()

        # Security Check: Ensure target is within root_path
        try:
            target.relative_to(self.root_path)
        except ValueError:
            raise SecurityError(f"Path traversal detected: '{ref_path}' escapes jail '{self.root_path}'")

        if not target.exists():
            raise FileNotFoundError(f"Referenced file not found: {target}")

        return target

    def _process_refs(self, data: Any, current_file: Path) -> Any:
        """
        Recursively traverse the data structure and resolve $ref fields.
        """
        if isinstance(data, dict):
            # Check for $ref
            if "$ref" in data:
                # If strictness requires validation of ONLY $ref or mixed content?
                # Usually {"$ref": "..."} replaces the node entirely.
                ref_path = data["$ref"]
                if not isinstance(ref_path, str):
                     raise ValueError(f"Invalid $ref value: {ref_path}")

                target_path = self._resolve_path(current_file.parent, ref_path)
                return self.load_file(target_path)

            # Recursive traversal for dict
            return {k: self._process_refs(v, current_file) for k, v in data.items()}

        elif isinstance(data, list):
            # Recursive traversal for list
            return [self._process_refs(item, current_file) for item in data]

        else:
            return data

    def load_file(self, path: Path | str) -> Any:
        """
        Load a file securely, resolving any recursive references.
        """
        path = Path(path).resolve()

        # Verify the file itself is within the jail
        try:
            path.relative_to(self.root_path)
        except ValueError:
             raise SecurityError(f"File outside jail: {path}")

        if not path.exists():
            raise FileNotFoundError(f"Manifest file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            content = f.read()

        try:
            # Validated: No regex checks or FORBIDDEN_PATTERNS (Security Theater removed)
            # The Citadel handles security via path confinement.
            data: dict[str, Any] = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse manifest file: {e}") from e

        # Recursively process references
        return self._process_refs(data, path)


def load_flow_from_file(path: str) -> LinearFlow | GraphFlow:
    """
    Load a flow manifest from a YAML or JSON file.
    Uses CitadelLoader to enforce security boundaries.

    Args:
        path: Path to the manifest file.

    Returns:
        LinearFlow | GraphFlow: The parsed flow object.

    Raises:
        ValueError: If the file content is invalid or the kind is unknown.
        FileNotFoundError: If the file does not exist.
        SecurityError: If a path traversal is detected.
    """
    file_path = Path(path).resolve()

    # Establish the Citadel Jail at the parent directory of the entry file
    # This allows referencing sibling files or files in subdirectories,
    # but strictly forbids traversing up the tree (e.g. ../../etc/passwd).
    jail_root = file_path.parent
    loader = CitadelLoader(jail_root)

    data = loader.load_file(file_path)

    if not isinstance(data, dict):
        raise ValueError("Manifest content must be a dictionary/object.")

    kind = data.get("kind")
    if kind == "LinearFlow":
        return LinearFlow.model_validate(data)
    if kind == "GraphFlow":
        return GraphFlow.model_validate(data)
    raise ValueError(f"Unknown or missing manifest kind: {kind}. Expected 'LinearFlow' or 'GraphFlow'.")
