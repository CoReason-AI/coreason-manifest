import contextlib
import errno
import os
import stat
import warnings
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

    def __init__(self, root_dir: Path, allow_external_refs: bool = False, strict_security: bool = True):
        """
        Initialize the secure loader.

        Args:
            root_dir: The root directory to confine file access to.
            allow_external_refs: Whether to allow loading files outside the root directory.
            strict_security: If True, enforce strict TOCTOU protections (requires O_NOFOLLOW).
        """
        self.jail = root_dir.resolve()
        self.allow_external = allow_external_refs

        if not hasattr(os, "O_NOFOLLOW"):
            if strict_security:
                raise OSError(
                    "Host OS lacks O_NOFOLLOW support. Strict TOCTOU security cannot be guaranteed. "
                    "Set strict_security=False to bypass this check at your own risk."
                )
            warnings.warn(
                "WARNING: TOCTOU protections disabled. Running on an OS without O_NOFOLLOW.",
                RuntimeWarning,
                stacklevel=2,
            )

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
            return f.read()

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
        except OSError as e:
            if e.errno == getattr(errno, "ELOOP", 40):
                raise SecurityViolationError(f"Symlink detected during path resolution: {path}") from e
            raise

        # 1. Path Traversal Check (High-Level)
        if not self.allow_external and not target_path.is_relative_to(self.jail):
            raise SecurityViolationError(f"Path Traversal Detected: {path}")

        # 2. LOW-LEVEL ATOMIC OPEN (TOCTOU Mitigation)
        # Defense in Depth: Check stats before opening to detect swaps
        try:
            stat_before = os.lstat(target_path)
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise FileNotFoundError(f"File not found or inaccessible: {path}") from e
            raise

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
            raise  # pragma: no cover

        try:
            # 3. CHECK PERMISSIONS ON THE DESCRIPTOR (Not the path)
            # This guarantees we are checking the actual file we just opened.
            st = os.fstat(fd)

            # Defense in depth: Verify inode and device
            if stat_before.st_ino == 0:
                warnings.warn(
                    "Inode heuristic blindspot: OS returned 0 for st_ino. Falling back to mtime/size.",
                    RuntimeWarning,
                    stacklevel=2,
                )
                if stat_before.st_mtime != st.st_mtime or stat_before.st_size != st.st_size:
                    raise SecurityViolationError("File swapped during open operation (mtime/size mismatch).")
            elif stat_before.st_ino != st.st_ino or stat_before.st_dev != st.st_dev:
                raise SecurityViolationError("File swapped during open operation (TOCTOU attack detected).")

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

            return content

        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse manifest file: {e}") from e


class ManifestDumper(yaml.SafeDumper):
    PRIORITY_KEYS = [
        "apiVersion",
        "type",
        "kind",
        "id",
        "name",
        "status",
        "metadata",
        "interface",
        "governance",
    ]
    DEPRIORITY_KEYS = ["definitions", "sequence", "steps", "graph", "nodes", "edges"]

    def represent_mapping(self, tag, mapping, flow_style=False):
        value = []
        node = yaml.MappingNode(tag, value, flow_style=flow_style)
        if self.alias_key is not None:
            self.represented_objects[self.alias_key] = node
        best_style = True
        if hasattr(mapping, "items"):
            mapping = list(mapping.items())

            # Custom sorting logic
            def sort_key(item):
                key = item[0]
                # specific safe string conversion for sorting
                key_str = str(key)

                if key_str in self.PRIORITY_KEYS:
                    return (0, self.PRIORITY_KEYS.index(key_str), key_str)
                elif key_str in self.DEPRIORITY_KEYS:
                    return (2, self.DEPRIORITY_KEYS.index(key_str), key_str)
                else:
                    return (1, key_str)

            mapping.sort(key=sort_key)

        for item_key, item_value in mapping:
            node_key = self.represent_data(item_key)
            node_value = self.represent_data(item_value)
            if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
                best_style = False
            if not (isinstance(node_value, yaml.ScalarNode) and not node_value.style):
                best_style = False
            value.append((node_key, node_value))

        if flow_style is None:
            if self.default_flow_style is not None:
                node.flow_style = self.default_flow_style
            else:
                node.flow_style = best_style
        return node


yaml.add_representer(dict, ManifestDumper.represent_dict, Dumper=ManifestDumper)


def export_manifest(model: Any, filepath: str | Path) -> None:
    payload = model.model_dump(exclude_none=True, by_alias=True)
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(
            payload,
            f,
            Dumper=ManifestDumper,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
