# src/coreason_manifest/utils/io.py

import contextlib
import errno
import os
import stat
from pathlib import Path
from typing import Any

import yaml


class SecurityViolationError(Exception):
    """Raised when a security constraint is violated during IO operations."""

    def __init__(self, message: str, code: str | None = None) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        prefix = f"Security Error: [{self.code}] " if self.code else "Security Error: "
        return f"{prefix}{self.message}"


class ManifestIO:
    """
    A secure file loader that enforces path confinement and permission checks.
    Acts as a 'Jail' to prevent Path Traversal attacks.
    """

    MAX_PAYLOAD_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_DEPTH = 50

    def __init__(self, root_dir: Path, allow_external_refs: bool = False):
        """
        Initialize the secure loader.

        Args:
            root_dir: The root directory to confine file access to.
            allow_external_refs: Whether to allow loading files outside the root directory.
        """
        self.jail = root_dir.resolve()
        self.allow_external = allow_external_refs

    @property
    def _is_posix(self) -> bool:
        """Check if the operating system is POSIX-compliant."""
        return os.name == "posix"

    def _read_from_fd(self, fd: int) -> str:
        """
        Read content from a file descriptor.
        This method takes ownership of the file descriptor via os.fdopen.
        """
        # Wrap the descriptor in a Python file object
        # Note: os.fdopen takes ownership of the fd, so closing 'f' closes 'fd'
        with os.fdopen(fd, "r", encoding="utf-8") as f:
            # SOTA: Read with limit to prevent DoS
            # We read strictly up to limit + 1 char to detect overflow eagerly.
            # Note: This is a character count check, effectively limiting memory usage.
            content = f.read(self.MAX_PAYLOAD_SIZE + 1)
            if len(content) > self.MAX_PAYLOAD_SIZE:
                raise SecurityViolationError(
                    f"Manifest payload exceeds limit of {self.MAX_PAYLOAD_SIZE} characters."
                )
            return content

    def read_text(self, path: str) -> str:
        """
        Read a file securely using low-level OS calls to prevent TOCTOU.
        Returns the raw string content.

        Args:
            path: Relative path to the file within the jail.

        Returns:
            The file content as a string.

        Raises:
            SecurityViolationError: If path traversal or unsafe permissions are detected.
            FileNotFoundError: If the file does not exist.
        """
        # Resolve path relative to jail
        file_path = Path(path)
        try:
            target_path = file_path.resolve() if file_path.is_absolute() else (self.jail / path).resolve()
        except RuntimeError as e:
            if "Symlink loop" in str(e):
                raise SecurityViolationError(f"Symlink detected during path resolution: {path}") from e
            raise  # pragma: no cover

        # 1. Path Traversal Check (High-Level)
        if not self.allow_external and not target_path.is_relative_to(self.jail):
            raise SecurityViolationError(f"Path Traversal Detected: {path}")

        # 2. LOW-LEVEL ATOMIC OPEN (TOCTOU Mitigation)
        try:
            # O_NOFOLLOW ensures we don't follow symlinks at the end of the path
            # O_RDONLY ensures read-only access
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(str(target_path), flags)
        except OSError as e:
            # Handle specific error codes
            if e.errno == getattr(errno, "ELOOP", 40):  # ELOOP = Too many symbolic links
                raise SecurityViolationError(f"Symlink detected (possible TOCTOU attack): {path}") from e
            if e.errno == errno.ENOENT:
                raise FileNotFoundError(f"File not found or inaccessible: {path}") from e
            raise e

        try:
            # 3. CHECK PERMISSIONS ON THE DESCRIPTOR (Not the path)
            # This guarantees we are checking the actual file we just opened.
            st = os.fstat(fd)

            if self._is_posix and (st.st_mode & stat.S_IWOTH):
                raise SecurityViolationError(f"Unsafe Permissions: {path} is world-writable.")

            # 4. READ CONTENT
            return self._read_from_fd(fd)

        except Exception:
            # Ensure FD is closed if os.fdopen failed or didn't take ownership
            # If os.fdopen succeeded, the 'with' block handles closing.
            # But if os.fdopen raised (e.g. bad mode), we must close fd manually.
            with contextlib.suppress(OSError):
                os.close(fd)
            raise

    def _enforce_depth_limit(self, data: Any, current_depth: int = 0) -> None:
        """
        Recursively checks the depth of the data structure.
        """
        if current_depth > self.MAX_DEPTH:
            raise SecurityViolationError(f"Manifest depth exceeds limit of {self.MAX_DEPTH}.")

        if isinstance(data, dict):
            for v in data.values():
                self._enforce_depth_limit(v, current_depth + 1)
        elif isinstance(data, list):
            for v in data:
                self._enforce_depth_limit(v, current_depth + 1)

    def load(self, path: str) -> dict[str, Any]:
        """
        Load a YAML/JSON file securely using low-level OS calls to prevent TOCTOU.

        Args:
            path: Relative path to the file within the jail.

        Returns:
            The parsed dictionary content.

        Raises:
            SecurityViolationError: If path traversal or unsafe permissions are detected.
            FileNotFoundError: If the file does not exist.
            ValueError: If the file content is invalid.
        """
        try:
            content_str = self.read_text(path)
            content = yaml.safe_load(content_str)

            if not isinstance(content, dict):
                raise ValueError("Manifest content must be a dictionary.")

            # Enforce depth limit
            self._enforce_depth_limit(content)

            return content

        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse manifest file: {e}") from e
