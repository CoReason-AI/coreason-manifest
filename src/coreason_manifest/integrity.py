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
      - Calculate the simple SHA256 of the source code directory.
      - Compare it against the integrity_hash defined in the manifest.
    """

    @staticmethod
    def calculate_directory_hash(source_dir: str | Path) -> str:
        """
        Calculates the SHA256 hash of a directory.

        The hash is calculated by:
        1. Walking the directory recursively.
        2. Sorting files by relative path (to ensure determinism).
        3. Reading each file's content and hashing it.
        4. Updating the global hash with the file path and its content hash.

        Args:
            source_dir: The path to the source code directory.

        Returns:
            str: The hex digest of the directory hash.

        Raises:
            FileNotFoundError: If the directory does not exist.
        """
        source_path = Path(source_dir)
        if not source_path.exists() or not source_path.is_dir():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        hasher = hashlib.sha256()

        # Gather all files
        files = []
        for p in source_path.rglob("*"):
            if p.is_file():
                # Store relative path to be independent of absolute location
                rel_path = p.relative_to(source_path).as_posix()
                files.append((rel_path, p))

        # Sort by relative path to ensure deterministic order
        files.sort(key=lambda x: x[0])

        for rel_path, abs_path in files:
            # Update hasher with file path
            hasher.update(rel_path.encode("utf-8"))

            # Update hasher with file content
            # Reading in chunks to handle large files
            with open(abs_path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hasher.update(chunk)

        return hasher.hexdigest()

    @staticmethod
    def verify(agent_def: AgentDefinition, source_dir: str | Path) -> None:
        """
        Verifies the integrity of the source code against the manifest.

        Args:
            agent_def: The AgentDefinition model (containing integrity_hash).
            source_dir: The path to the source code directory.

        Raises:
            IntegrityCompromisedError: If hashes mismatch or integrity_hash is missing.
            FileNotFoundError: If source directory is not found.
        """
        if not agent_def.integrity_hash:
            raise IntegrityCompromisedError("Manifest is missing 'integrity_hash'. Cannot verify integrity.")

        calculated_hash = IntegrityChecker.calculate_directory_hash(source_dir)

        if calculated_hash != agent_def.integrity_hash:
            raise IntegrityCompromisedError(
                f"Integrity check failed. Expected {agent_def.integrity_hash}, but calculated {calculated_hash}."
            )
