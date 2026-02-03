# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Resolver module for secure file reference handling."""

from pathlib import Path
from typing import Union


class ReferenceResolver:
    """Resolves file references with security constraints (Jail)."""

    def __init__(self, root_dir: Union[str, Path]):
        """
        Initialize the resolver with a root directory.

        Args:
            root_dir: The allowed jail directory. All resolved paths must be within this directory.
        """
        self.root_dir = Path(root_dir).resolve()

    def resolve(self, base_file: Path, ref_path: str) -> Path:
        """
        Resolve a reference relative to a base file, ensuring it stays within the root directory.

        Args:
            base_file: The file containing the reference.
            ref_path: The relative path string to resolve.

        Returns:
            The absolute resolved Path.

        Raises:
            ValueError: If the resolved path escapes the root directory.
            FileNotFoundError: If the referenced file does not exist.
        """
        # Ensure base_file is absolute
        base_file = base_file.resolve()

        # Combine base_file parent with ref_path
        # We assume ref_path is relative to the base_file's location
        target_path = (base_file.parent / ref_path).resolve()

        # Security Check: Jail
        try:
            target_path.relative_to(self.root_dir)
        except ValueError:
            raise ValueError(
                f"Security Error: Reference '{ref_path}' escapes the root directory '{self.root_dir}'."
            ) from None

        if not target_path.exists():
            raise FileNotFoundError(f"Referenced file not found: {target_path}")

        return target_path
