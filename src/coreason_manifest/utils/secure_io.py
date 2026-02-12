from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


class SecurityError(Exception):
    """Raised when a file access violates security policies."""

class SecureLoader:
    """
    A secure file loader that enforces jail restrictions and resolves references.
    """

    def __init__(self, root_dir: Path) -> None:
        """
        Initialize the SecureLoader with a trusted root directory (jail).
        """
        self.root_dir = root_dir.resolve()

    def resolve_ref(self, current_file: Path, ref: str) -> Path:
        """
        Resolve a reference relative to the current file, ensuring it stays within the jail.
        """
        # Resolve the path relative to the current file's directory
        resolved_path = (current_file.parent / ref).resolve()

        # Enforce the jail
        try:
            # os.path.commonpath raises ValueError if paths are on different drives
            common = os.path.commonpath([str(resolved_path), str(self.root_dir)])
            if common != str(self.root_dir):
                raise SecurityError(f"Access denied: Path '{resolved_path}' attempts to escape jail '{self.root_dir}'")
        except ValueError as e:
            raise SecurityError(
                f"Access denied: Path '{resolved_path}' is on a different drive than jail '{self.root_dir}'"
            ) from e

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {resolved_path}")

        return resolved_path

    def load(self, path: Path) -> dict[str, Any]:
        """
        Load a YAML file and recursively resolve all "$ref" dependencies.
        """
        path = path.resolve()

        # Verify the initial file is also within the jail
        try:
            common = os.path.commonpath([str(path), str(self.root_dir)])
            if common != str(self.root_dir):
                raise SecurityError(f"Initial file '{path}' is outside the jail '{self.root_dir}'")
        except ValueError as e:
            raise SecurityError(f"Initial file '{path}' is outside the jail '{self.root_dir}'") from e

        return self._load_recursive(path, set())

    def _load_recursive(self, path: Path, visited: set[Path]) -> Any:
        if path in visited:
            raise RecursionError(f"Circular dependency detected: {path}")

        # Create a new set for the current path to allow diamond dependencies
        # (A -> B, A -> C, B -> D, C -> D)
        # If we modified visited in place, D would be visited via B, then rejected via C.
        new_visited = visited | {path}

        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return self._scan_and_resolve(data, path, new_visited)

    def _scan_and_resolve(self, data: Any, current_file: Path, visited: set[Path]) -> Any:
        if isinstance(data, dict):
            if "$ref" in data:
                ref = data["$ref"]
                if not isinstance(ref, str):
                     raise ValueError(f"Invalid $ref value in {current_file}: {ref}")

                resolved_path = self.resolve_ref(current_file, ref)
                return self._load_recursive(resolved_path, visited)

            return {k: self._scan_and_resolve(v, current_file, visited) for k, v in data.items()}

        if isinstance(data, list):
            return [self._scan_and_resolve(item, current_file, visited) for item in data]

        return data
