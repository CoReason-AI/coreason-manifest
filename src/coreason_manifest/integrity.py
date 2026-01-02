# Prosperity-3.0
from __future__ import annotations

import hashlib
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

    @staticmethod
    def calculate_hash(source_dir: Path | str) -> str:
        """
        Calculates a deterministic SHA256 hash of the source code directory.

        It walks the directory, sorts files by relative path, hashes each file,
        and then hashes the sequence of file hashes.

        Args:
            source_dir: The directory containing source code.

        Returns:
            The hex digest of the SHA256 hash.

        Raises:
            FileNotFoundError: If source_dir does not exist.
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_path}")

        sha256 = hashlib.sha256()

        # Collect all file paths relative to source_dir
        file_paths = []
        for path in source_path.rglob("*"):
            if path.is_file():
                file_paths.append(path)

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
