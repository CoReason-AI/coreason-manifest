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

        It walks the directory, sorts files by relative path, hashes each file,
        and then hashes the sequence of file hashes.

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

        # Collect all file paths relative to source_dir
        file_paths = []

        # Use os.walk to efficiently prune ignored directories
        for root, dirs, files in os.walk(source_path, followlinks=False):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in IntegrityChecker.IGNORED_DIRS]

            root_path = Path(root)

            # Check for directory symlinks (os.walk with followlinks=False returns them in dirs,
            # but we also need to be careful about the root itself if it was a symlink passed in,
            # though pathlib handles that check before).
            # Here we check if any of the *files* are symlinks.
            # We also need to check if we are traversing a symlinked directory if we didn't want to.
            # But followlinks=False ensures we don't descend into them.
            # However, we must strictly FORBID them as per spec.

            for name in files:
                file_path = root_path / name

                if file_path.is_symlink():
                    raise IntegrityCompromisedError(f"Symbolic links are forbidden: {file_path}")

                if name in IntegrityChecker.IGNORED_DIRS:
                    continue

                file_paths.append(file_path)

            # Also check if any subdirectory is a symlink (even if we don't follow it)
            # because the spec implies strict "Clean Room" rules.
            for name in dirs:
                dir_path = root_path / name
                if dir_path.is_symlink():
                    raise IntegrityCompromisedError(f"Symbolic links are forbidden: {dir_path}")

        # Sort to ensure deterministic order
        file_paths.sort(key=lambda p: p.relative_to(source_path))

        for path in file_paths:
            # Update hash with relative path to ensure structure matters
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
