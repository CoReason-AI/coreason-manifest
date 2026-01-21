# Prosperity-3.0
"""Integrity checking functionality.

This module provides the `IntegrityChecker` class, which is responsible for
calculating deterministic hashes of source code directories and verifying
them against the expected hash in the agent manifest.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import List, Optional, Set, Union

from coreason_manifest.errors import IntegrityCompromisedError
from coreason_manifest.models import AgentDefinition


class IntegrityChecker:
    """Component D: IntegrityChecker (The Notary).

    Responsibility:
      - Calculate the SHA256 hash of the source code directory.
      - Compare it against the integrity_hash defined in the manifest.
    """

    IGNORED_DIRS = frozenset({".git", "__pycache__", ".venv", ".env", ".DS_Store"})

    @staticmethod
    def calculate_hash(source_dir: Union[Path, str], exclude_files: Optional[Set[Union[Path, str]]] = None) -> str:
        """Calculates a deterministic SHA256 hash of the source code directory.

        It walks the directory using os.walk to efficiently prune ignored directories.
        Sorts files by relative path, hashes each file, and then hashes the sequence.

        Ignores hidden directories/files in IGNORED_DIRS.
        Rejects symbolic links for security.

        Args:
            source_dir: The directory containing source code.
            exclude_files: Optional set of file paths (absolute or relative to CWD)
                to exclude from hashing.

        Returns:
            The hex digest of the SHA256 hash.

        Raises:
            FileNotFoundError: If source_dir does not exist.
            IntegrityCompromisedError: If a symlink is found.
        """
        path_obj = Path(source_dir)
        if path_obj.is_symlink():
            raise IntegrityCompromisedError(f"Symbolic links are forbidden: {path_obj}")

        source_path = path_obj.resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_path}")

        # Normalize excluded files to absolute paths
        excludes = set()
        if exclude_files:
            for ex_path in exclude_files:
                excludes.add(Path(ex_path).resolve())

        sha256 = hashlib.sha256()
        file_paths: List[Path] = []

        # Use os.walk for efficient traversal and pruning
        for root, dirs, files in os.walk(source_path, topdown=True):
            root_path = Path(root)

            # Check for symlinks in directories before pruning
            for d_name in dirs:
                d_path = root_path / d_name
                if d_path.is_symlink():
                    raise IntegrityCompromisedError(f"Symbolic links are forbidden: {d_path}")  # pragma: no cover

            # Prune directories efficiently using slice assignment
            dirs[:] = [d for d in dirs if d not in IntegrityChecker.IGNORED_DIRS]

            # Collect files
            for f_name in files:
                f_path = root_path / f_name

                if f_path.is_symlink():
                    raise IntegrityCompromisedError(f"Symbolic links are forbidden: {f_path}")

                if f_name in IntegrityChecker.IGNORED_DIRS:
                    continue

                # Use resolved path for exclusion checking and inclusion
                f_path_abs = f_path.resolve()
                if f_path_abs in excludes:
                    continue

                file_paths.append(f_path_abs)

        # Sort to ensure deterministic order
        # Use as_posix() to ensure ASCII sorting (case-sensitive) on all platforms (Windows vs Linux)
        file_paths.sort(key=lambda p: p.relative_to(source_path).as_posix())

        for path in file_paths:
            # Update hash with relative path to ensure structure matters
            # Use forward slashes for cross-platform consistency
            rel_path = path.relative_to(source_path).as_posix().encode("utf-8")
            sha256.update(rel_path)

            # Update hash with file content
            with open(path, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)

        return sha256.hexdigest()

    @staticmethod
    def verify(
        agent_def: AgentDefinition,
        source_dir: Union[Path, str],
        manifest_path: Optional[Union[Path, str]] = None,
    ) -> None:
        """Verifies the integrity of the source code against the manifest.

        Args:
            agent_def: The AgentDefinition containing the expected hash.
            source_dir: The directory containing source code.
            manifest_path: Optional path to the manifest file to exclude from hashing.

        Raises:
            IntegrityCompromisedError: If the hash does not match or is missing.
            FileNotFoundError: If source_dir does not exist.
        """
        exclude_files = {manifest_path} if manifest_path else None

        # agent_def.integrity_hash is now required by Pydantic model
        calculated = IntegrityChecker.calculate_hash(source_dir, exclude_files=exclude_files)

        if calculated != agent_def.integrity_hash:
            raise IntegrityCompromisedError(
                f"Integrity check failed. Expected {agent_def.integrity_hash}, got {calculated}"
            )
