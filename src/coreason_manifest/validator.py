# Prosperity-3.0
from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any, cast

import jsonschema
from jsonschema.validators import validator_for

from coreason_manifest.errors import SchemaValidationError


class SchemaValidator:
    """
    Component B: SchemaValidator (The Structural Engineer).

    Responsibility:
      - Validate the dictionary against the Master JSON Schema.
      - Check required fields, data types, and format constraints.
    """

    def __init__(self, schema_path: str | Path | None = None) -> None:
        """
        Initialize the SchemaValidator.

        Args:
            schema_path: Path to the JSON schema file. If None, loads the bundled agent.schema.json.
        """
        if schema_path:
            self.schema = self._load_schema_from_path(Path(schema_path))
        else:
            self.schema = self._load_bundled_schema()

        # Create a validator instance
        validator_cls = validator_for(self.schema)
        # We need to configure the validator to support format checking if needed (e.g. date-time, uuid)
        # The jsonschema library requires explicitly passing a format checker.
        self.validator = validator_cls(self.schema, format_checker=jsonschema.FormatChecker())

    def _load_schema_from_path(self, path: Path) -> dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return cast(dict[str, Any], data)

    def _load_bundled_schema(self) -> dict[str, Any]:
        # Locate the schema file within the package
        # Assuming schemas are in src/coreason_manifest/schemas/
        try:
            from coreason_manifest import schemas

            schema_file = resources.files(schemas) / "agent.schema.json"
            with schema_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return cast(dict[str, Any], data)
        except (ImportError, FileNotFoundError) as e:
            # Fallback for when running in an environment where resources aren't packaged yet?
            # Or if the path is slightly different.
            # Try relative path from this file
            current_dir = Path(__file__).parent
            schema_path = current_dir / "schemas" / "agent.schema.json"
            if schema_path.exists():
                return self._load_schema_from_path(schema_path)
            raise FileNotFoundError("Could not locate agent.schema.json in package resources.") from e

    def validate(self, data: dict[str, Any]) -> bool:
        """
        Validates the raw dictionary against the JSON schema.

        Args:
            data: The raw dictionary to validate.

        Returns:
            bool: True if validation succeeds.

        Raises:
            SchemaValidationError: If validation fails, containing a list of errors.
        """
        errors = list(self.validator.iter_errors(data))
        if not errors:
            return True

        # Format errors into a readable list
        error_messages = []
        for error in errors:
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            error_messages.append(f"{path}: {error.message}")

        raise SchemaValidationError("Schema validation failed.", errors=error_messages)
