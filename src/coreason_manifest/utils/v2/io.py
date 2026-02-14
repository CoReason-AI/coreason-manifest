# src/coreason_manifest/utils/v2/io.py

import os
import stat
from pathlib import Path
from typing import Any

import yaml


class SecurityViolation(Exception):
    """Raised when a security constraint is violated during IO operations."""
    pass


class ManifestIO:
    """
    A secure file loader that enforces path confinement and permission checks.
    Acts as a 'Jail' to prevent Path Traversal attacks.
    """

    def __init__(self, root_dir: Path, allow_external_refs: bool = False):
        """
        Initialize the secure loader.

        Args:
            root_dir: The root directory to confine file access to.
            allow_external_refs: Whether to allow loading files outside the root directory.
        """
        self.jail = root_dir.resolve()
        self.allow_external = allow_external_refs

    def load(self, path: str) -> dict[str, Any]:
        """
        Load a YAML/JSON file securely.

        Args:
            path: Relative path to the file within the jail.

        Returns:
            The parsed dictionary content.

        Raises:
            SecurityViolation: If path traversal or unsafe permissions are detected.
            FileNotFoundError: If the file does not exist.
            ValueError: If the file content is invalid.
        """
        # Resolve path relative to jail
        # Note: If path is absolute, (self.jail / path) will ignore self.jail.
        # We must protect against absolute paths if they are outside jail.
        file_path = Path(path)
        if file_path.is_absolute():
            target_path = file_path.resolve()
        else:
            target_path = (self.jail / path).resolve()

        # 1. Path Traversal Check
        # Ensure the resolved path starts with the jail path
        if not self.allow_external:
            try:
                target_path.relative_to(self.jail)
            except ValueError:
                raise SecurityViolation(f"Path Traversal Detected: {path}")

        if not target_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {path}")

        # 2. POSIX Permission Check
        if os.name == "posix":
            st = target_path.stat()
            # Check for world-writable (S_IWOTH)
            if st.st_mode & stat.S_IWOTH:
                raise SecurityViolation(f"Unsafe Permissions: {path} is world-writable.")

        try:
            with target_path.open("r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                if not isinstance(content, dict):
                    raise ValueError("Manifest content must be a dictionary/object.")
                return content
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse manifest file: {e}") from e
