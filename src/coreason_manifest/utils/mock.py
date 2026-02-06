# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import random
import string
import uuid
from datetime import UTC, datetime
from typing import Any

from coreason_manifest.spec.v2.definitions import AgentDefinition


class MockGenerator:
    def __init__(self, seed: int | None = None, definitions: dict[str, Any] | None = None, max_depth: int = 10) -> None:
        self.rng = random.Random(seed)
        self.definitions = definitions or {}
        self.max_depth = max_depth

    def _random_string(self, min_len: int = 5, max_len: int = 20) -> str:
        length = self.rng.randint(min_len, max_len)
        chars = string.ascii_letters + string.digits + " "
        return "".join(self.rng.choices(chars, k=length))

    def _random_int(self, min_val: int = 0, max_val: int = 100) -> int:
        return self.rng.randint(min_val, max_val)

    def _random_float(self) -> float:
        return self.rng.uniform(0.0, 100.0)

    def _random_bool(self) -> bool:
        return self.rng.choice([True, False])

    def _generate_value(self, schema: dict[str, Any], depth: int = 0) -> Any:
        if not schema:
            return {}

        if depth > self.max_depth:
            # Stop recursion
            return None

        # Handle const
        if "const" in schema:
            return schema["const"]

        # Handle $ref
        if "$ref" in schema:
            ref = schema["$ref"]
            # Usually ref is "#/$defs/MyModel" or "#/definitions/MyModel"
            # We assume simple local refs for now
            parts = ref.split("/")
            ref_name = parts[-1]
            if ref_name in self.definitions:
                return self._generate_value(self.definitions[ref_name], depth + 1)
            # Fallback if not found
            return {}

        # Handle enum
        if "enum" in schema:
            return self.rng.choice(schema["enum"])

        # Handle type
        type_ = schema.get("type")

        # Handle list of types (e.g. ["string", "null"])
        if isinstance(type_, list):
            # Prefer non-null types if available
            valid_types = [t for t in type_ if t != "null"]
            type_ = self.rng.choice(valid_types) if valid_types else "null"

        if type_ == "string":
            format_ = schema.get("format")
            if format_ == "date-time":
                # Deterministic time if seed is provided
                base_time = datetime(2024, 1, 1, tzinfo=UTC).timestamp()
                random_offset = self.rng.uniform(0, 365 * 24 * 3600)
                return datetime.fromtimestamp(base_time + random_offset, tz=UTC).isoformat()
            if format_ == "uuid":
                return str(uuid.UUID(int=self.rng.getrandbits(128)))
            return self._random_string()

        if type_ == "integer":
            return self._random_int()

        if type_ == "number":
            return self._random_float()

        if type_ == "boolean":
            return self._random_bool()

        if type_ == "null":
            return None

        if type_ == "array":
            items_schema = schema.get("items", {})
            length = self.rng.randint(1, 3)
            return [self._generate_value(items_schema, depth + 1) for _ in range(length)]

        if type_ == "object":
            properties = schema.get("properties", {})
            result = {}
            for key, prop_schema in properties.items():
                result[key] = self._generate_value(prop_schema, depth + 1)
            return result

        # Fallback for unknown type
        return None


def generate_mock_output(agent: AgentDefinition, seed: int | None = None) -> dict[str, Any]:
    """
    Generates a valid dictionary matching the agent's output schema.
    """
    # 1. Extract definitions if available (usually in interface.outputs.get('$defs'))
    outputs_schema = agent.interface.outputs
    definitions = outputs_schema.get("$defs") or outputs_schema.get("definitions") or {}

    # 2. Initialize MockGenerator with seed.
    generator = MockGenerator(seed=seed, definitions=definitions)

    # 3. Call generator._generate_value(agent.interface.outputs)
    result = generator._generate_value(outputs_schema)
    if isinstance(result, dict):
        return result
    return {}  # Should return dict per signature
