# Prosperity-3.0
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from coreason_manifest.errors import IntegrityCompromisedError
from coreason_manifest.models import AgentDefinition


class IntegrityChecker:
    """
    Component D: IntegrityChecker (The Notary).

    Responsibility:
      - Calculate the SHA256 hash of the source code directory.
      - Compare it against the integrity_hash defined in the manifest.
    """

    IGNORED_DIRS = {".git", "__pycache__", ".venv", ".env", ".DS_Store"}

    @staticmethod
    def calculate_hash(source_dir: Path | str) -> str:
        """
        Calculates a deterministic SHA256 hash of the source code directory.

        It walks the directory using os.walk to efficiently prune ignored directories.
        Sorts files by relative path, hashes each file, and then hashes the sequence.

        Ignores hidden directories/files in IGNORED_DIRS.
        Rejects symbolic links for security.

        Args:
            source_dir: The directory containing source code.

        Returns:
            The hex digest of the SHA256 hash.

        Raises:
            FileNotFoundError: If source_dir does not exist.
            IntegrityCompromisedError: If a symlink is found.
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_path}")

        sha256 = hashlib.sha256()
        file_paths = []

        # Use os.walk for efficient traversal and pruning
        for root, dirs, files in os.walk(source_path, topdown=True):
            root_path = Path(root)

            # Check if the root itself is a symlink (edge case if source_dir is a symlink)
            if root_path.is_symlink():
                raise IntegrityCompromisedError(f"Symbolic links are forbidden: {root_path}")

            # Prune directories
            # We must iterate manually to modify 'dirs' in-place
            i = 0
            while i < len(dirs):
                d_name = dirs[i]
                d_path = root_path / d_name

                if d_path.is_symlink():
                    raise IntegrityCompromisedError(f"Symbolic links are forbidden: {d_path}")

                if d_name in IntegrityChecker.IGNORED_DIRS:
                    del dirs[i]
                else:
                    i += 1

            # Collect files
            for f_name in files:
                f_path = root_path / f_name

                if f_path.is_symlink():
                    raise IntegrityCompromisedError(f"Symbolic links are forbidden: {f_path}")

                if f_name in IntegrityChecker.IGNORED_DIRS:
                    continue

                file_paths.append(f_path)

        # Sort to ensure deterministic order
        file_paths.sort(key=lambda p: p.relative_to(source_path))

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
    def verify(agent_def: AgentDefinition, source_dir: Path | str) -> None:
        """
        Verifies the integrity of the source code against the manifest.

        Args:
            agent_def: The AgentDefinition containing the expected hash.
            source_dir: The directory containing source code.

        Raises:
            IntegrityCompromisedError: If the hash does not match or is missing.
            FileNotFoundError: If source_dir does not exist.
        """
        if not agent_def.integrity_hash:
            raise IntegrityCompromisedError("Manifest missing integrity_hash.")

        calculated = IntegrityChecker.calculate_hash(source_dir)

        if calculated != agent_def.integrity_hash:
            raise IntegrityCompromisedError(
                f"Integrity check failed. Expected {agent_def.integrity_hash}, got {calculated}"
            )
