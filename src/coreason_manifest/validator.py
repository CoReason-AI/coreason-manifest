# Prosperity-3.0
"""Schema validation functionality.

This module provides the `SchemaValidator` class, which uses JSON Schema to
validate the structure and types of agent definitions.
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from jsonschema import FormatChecker, ValidationError, validate

from coreason_manifest.errors import ManifestSyntaxError


class SchemaValidator:
    """Component B: SchemaValidator (The Structural Engineer).

    Responsibility:
      - Validate the dictionary against the Master JSON Schema.
      - Check required fields, data types, and format constraints.
    """

    def __init__(self) -> None:
        """Initialize the validator by loading the schema."""
        self.schema = self._load_schema()

    def _load_schema(self) -> dict[str, Any]:
        """Loads the JSON schema from the package resources.

        Returns:
            The JSON schema dictionary.

        Raises:
            ManifestSyntaxError: If the schema file cannot be loaded or is invalid.
        """
        try:
            schema_path = files("coreason_manifest.schemas").joinpath("agent.schema.json")
            with schema_path.open("r", encoding="utf-8") as f:
                schema = json.load(f)
            if not isinstance(schema, dict):
                raise ManifestSyntaxError("Schema file is not a valid JSON object.")
            return schema
        except (IOError, json.JSONDecodeError) as e:
            raise ManifestSyntaxError(f"Failed to load agent schema: {e}") from e

    def validate(self, data: dict[str, Any]) -> bool:
        """Validates the given dictionary against the agent schema.

        Args:
            data: The raw dictionary to validate.

        Returns:
            True if validation passes.

        Raises:
            ManifestSyntaxError: If validation fails.
        """
        try:
            validate(instance=data, schema=self.schema, format_checker=FormatChecker())
            return True
        except ValidationError as e:
            # We treat schema validation errors as syntax errors in the manifest
            raise ManifestSyntaxError(f"Schema validation failed: {e.message}") from e
