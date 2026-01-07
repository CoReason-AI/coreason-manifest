# Prosperity-3.0
from __future__ import annotations

from pathlib import Path
from typing import Any, Union

import yaml
from pydantic import ValidationError

from coreason_manifest.errors import ManifestSyntaxError
from coreason_manifest.models import AgentDefinition


class ManifestLoader:
    """
    Component A: ManifestLoader (The Parser).

    Responsibility:
      - Load YAML safely.
      - Convert raw data into a Pydantic AgentDefinition model.
      - Normalization: Ensure all version strings follow SemVer and all IDs are canonical UUIDs.
    """

    @staticmethod
    def load_raw_from_file(path: Union[str, Path]) -> dict[str, Any]:
        """
        Loads the raw dict from a YAML file.

        Args:
            path: The path to the agent.yaml file.

        Returns:
            dict: The raw dictionary content.

        Raises:
            ManifestSyntaxError: If YAML is invalid.
            FileNotFoundError: If the file does not exist.
        """
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise FileNotFoundError(f"Manifest file not found: {path}")

            with open(path_obj, "r", encoding="utf-8") as f:
                # safe_load is recommended for untrusted input
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise ManifestSyntaxError(f"Invalid YAML content in {path}: must be a dictionary.")

            # Normalization logic is now centralized in load_from_dict
            # But we perform it here too if we return the raw dict, or we delegate.
            # However, standardizing on load_from_dict doing the normalization is cleaner.
            # But for backward compatibility with callers who use raw dict, we keep the logic here too?
            # Or we call a shared helper. For now, we replicate or keep it.
            # Actually, the requirement is "explicitly strip ... before they reach Pydantic models".
            # If load_raw returns data, and then user calls load_from_dict, load_from_dict must do it.
            # If load_raw returns data with 'v', the caller sees 'v'. That's fine for raw.
            # But let's apply it here too for consistency.

            ManifestLoader._normalize_data(data)

            return data

        except yaml.YAMLError as e:
            raise ManifestSyntaxError(f"Failed to parse YAML file {path}: {str(e)}") from e
        except OSError as e:
            if isinstance(e, FileNotFoundError):
                raise
            raise ManifestSyntaxError(f"Error reading file {path}: {str(e)}") from e

    @staticmethod
    def load_from_file(path: Union[str, Path]) -> AgentDefinition:
        """
        Loads the agent manifest from a YAML file.

        Args:
            path: The path to the agent.yaml file.

        Returns:
            AgentDefinition: The validated Pydantic model.

        Raises:
            ManifestSyntaxError: If YAML is invalid or Pydantic validation fails.
            FileNotFoundError: If the file does not exist.
        """
        data = ManifestLoader.load_raw_from_file(path)
        return ManifestLoader.load_from_dict(data)

    @staticmethod
    def load_from_dict(data: dict[str, Any]) -> AgentDefinition:
        """
        Converts a dictionary into an AgentDefinition model.

        Args:
            data: The raw dictionary.

        Returns:
            AgentDefinition: The validated Pydantic model.

        Raises:
            ManifestSyntaxError: If Pydantic validation fails.
        """
        try:
            # Ensure normalization happens before Pydantic validation
            # We work on a copy to avoid side effects if possible, but deep copy is expensive.
            # The input 'data' might be modified in place.
            ManifestLoader._normalize_data(data)

            return AgentDefinition.model_validate(data)
        except ValidationError as e:
            # Convert Pydantic ValidationError to ManifestSyntaxError
            # We assume "normalization" happens via Pydantic validators (e.g. UUID, SemVer checks)
            raise ManifestSyntaxError(f"Manifest validation failed: {str(e)}") from e

    @staticmethod
    def _normalize_data(data: dict[str, Any]) -> None:
        """
        Normalizes the data dictionary in place.
        Specifically strips 'v' or 'V' from version strings.
        """
        if "metadata" in data and isinstance(data["metadata"], dict):
            version = data["metadata"].get("version")
            if isinstance(version, str) and version.lower().startswith("v"):
                data["metadata"]["version"] = version[1:]
