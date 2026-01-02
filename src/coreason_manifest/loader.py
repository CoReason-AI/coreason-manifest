# Prosperity-3.0
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Union

from pydantic import ValidationError

from coreason_manifest.models import AgentDefinition
from coreason_manifest.errors import ManifestSyntaxError


class ManifestLoader:
    """
    Component A: ManifestLoader (The Parser).

    Responsibility:
      - Load YAML safely.
      - Convert raw data into a Pydantic AgentDefinition model.
      - Normalization: Ensure all version strings follow SemVer and all IDs are canonical UUIDs.
    """

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
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise FileNotFoundError(f"Manifest file not found: {path}")

            with open(path_obj, "r", encoding="utf-8") as f:
                # safe_load is recommended for untrusted input
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise ManifestSyntaxError(f"Invalid YAML content in {path}: must be a dictionary.")

            return ManifestLoader.load_from_dict(data)

        except yaml.YAMLError as e:
            raise ManifestSyntaxError(f"Failed to parse YAML file {path}: {str(e)}") from e
        except OSError as e:
            # FileNotFoundError is an OSError, but we want to bubble it up or wrap it?
            # The docstring says raises FileNotFoundError, so we let it bubble.
            # But other OS errors might happen.
            if isinstance(e, FileNotFoundError):
                raise
            raise ManifestSyntaxError(f"Error reading file {path}: {str(e)}") from e

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
            return AgentDefinition.model_validate(data)
        except ValidationError as e:
            # Convert Pydantic ValidationError to ManifestSyntaxError
            # We assume "normalization" happens via Pydantic validators (e.g. UUID, SemVer checks)
            raise ManifestSyntaxError(f"Manifest validation failed: {str(e)}") from e
