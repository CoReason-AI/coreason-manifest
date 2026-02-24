import contextlib
import errno
import os
import stat
import warnings
from pathlib import Path
from typing import Any, ClassVar

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
    """Custom PyYAML Dumper that enforces a strict 'Aesthetic Contract' for manifests."""

    _PRIORITY_KEYS: ClassVar[list[str]] = [
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
    _DEPRIORITY_KEYS: ClassVar[list[str]] = ["definitions", "sequence", "steps", "graph", "nodes", "edges"]

    # SOTA: Pre-compute O(1) lookup maps to prevent O(N) list scans during sorting
    _PRIORITY_MAP: ClassVar[dict[str, int]] = {k: i for i, k in enumerate(_PRIORITY_KEYS)}
    _DEPRIORITY_MAP: ClassVar[dict[str, int]] = {k: i for i, k in enumerate(_DEPRIORITY_KEYS)}


def _dict_representer(dumper: ManifestDumper, data: dict[str, Any]) -> yaml.MappingNode:
    """Sorts dictionaries aesthetically before yielding them to the YAML engine."""

    def sort_key(item: tuple[Any, Any]) -> tuple[int, int, str]:
        key = str(item[0])
        if key in ManifestDumper._PRIORITY_MAP:
            return (0, ManifestDumper._PRIORITY_MAP[key], key)
        if key in ManifestDumper._DEPRIORITY_MAP:
            return (2, ManifestDumper._DEPRIORITY_MAP[key], key)
        # Default middle priority. Use 0 as stable secondary sort index to maintain tuple symmetry.
        return (1, 0, key)

    # Python 3.7+ guarantees insertion order preservation
    sorted_dict = dict(sorted(data.items(), key=sort_key))

    # Safely delegate back to PyYAML's native node generation
    return dumper.represent_mapping("tag:yaml.org,2002:map", sorted_dict)


# Register strictly on our custom dumper to avoid polluting the global yaml.SafeDumper
ManifestDumper.add_representer(dict, _dict_representer)


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
