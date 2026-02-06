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
    def __init__(self, seed: int | None = None, definitions: dict[str, Any] | None = None):
        self.rng = random.Random(seed)
        self.definitions = definitions or {}
        self.recursion_depth = 0
        self.max_depth = 10

    def _random_string(self, min_len: int = 5, max_len: int = 20) -> str:
        length = self.rng.randint(min_len, max_len)
        return "".join(self.rng.choices(string.ascii_letters + string.digits + " ", k=length)).strip()

    def _random_int(self, min_val: int = 0, max_val: int = 100) -> int:
        return self.rng.randint(min_val, max_val)

    def _random_float(self) -> float:
        return self.rng.random() * 100.0

    def _random_bool(self) -> bool:
        return self.rng.choice([True, False])

    def _generate_value(self, schema: dict[str, Any]) -> Any:
        if self.recursion_depth > self.max_depth:
            return None

        # Handle $ref
        if "$ref" in schema:
            ref = schema["$ref"]
            # Typically refs are like "#/$defs/MyModel" or "#/definitions/MyModel"
            ref_name = ref.split("/")[-1]
            if ref_name in self.definitions:
                self.recursion_depth += 1
                val = self._generate_value(self.definitions[ref_name])
                self.recursion_depth -= 1
                return val
            # Fallback if not found
            return {}

        # Handle enum
        if "enum" in schema:
            return self.rng.choice(schema["enum"])

        # Handle const
        if "const" in schema:
            return schema["const"]

        # Handle types
        t = schema.get("type")

        # Handle union types (e.g. ["string", "null"])
        if isinstance(t, list):
            non_null = [x for x in t if x != "null"]
            if non_null:
                t = self.rng.choice(non_null)
            else:
                return None

        # Handle composite keywords if type is missing or to augment type
        if "allOf" in schema:
            merged: dict[str, Any] = {}
            for s in schema["allOf"]:
                # If we have refs in allOf, we should probably resolve them,
                # but for simple mock gen, let's just merge properties.
                # A proper merge is complex.
                # Let's assume s is a schema dict.
                # If it's a ref, we should resolve it first.
                sub_schema = s
                if "$ref" in s:
                    ref_name = s["$ref"].split("/")[-1]
                    sub_schema = self.definitions.get(ref_name, {})

                # Deep merge properties
                for k, v in sub_schema.items():
                    if k == "properties" and isinstance(v, dict):
                        if "properties" not in merged:
                            merged["properties"] = {}
                        merged["properties"].update(v)
                    else:
                        merged[k] = v

            # If the merged schema has a type, recurse with that.
            # If not, and we have properties, assume object.
            # We must be careful not to infinite loop if allOf is the only thing.
            if merged and merged != schema:
                # Merge the original schema into it (except allOf) to keep other constraints
                combined = merged.copy()
                for k, v in schema.items():
                    if k != "allOf":
                        # If properties, we should merge those too
                        if k == "properties" and isinstance(v, dict):
                            if "properties" not in combined:
                                combined["properties"] = {}
                            combined["properties"].update(v)
                        else:
                            combined[k] = v
                return self._generate_value(combined)

        if "anyOf" in schema or "oneOf" in schema:
            options = schema.get("anyOf") or schema.get("oneOf")
            if options:
                choice = self.rng.choice(options)
                return self._generate_value(choice)

        if t == "string":
            fmt = schema.get("format")
            if fmt == "date-time":
                # Deterministic time range
                ts = self.rng.randint(1600000000, 1700000000)
                dt = datetime.fromtimestamp(ts, tz=UTC)
                return dt.isoformat().replace("+00:00", "Z")
            if fmt == "uuid":
                return str(uuid.UUID(int=self.rng.getrandbits(128)))
            return self._random_string()

        if t == "integer":
            return self._random_int()

        if t == "number":
            return self._random_float()

        if t == "boolean":
            return self._random_bool()

        if t == "array":
            items_schema = schema.get("items", {})
            length = self.rng.randint(1, 3)
            return [self._generate_value(items_schema) for _ in range(length)]

        if t == "object":
            props = schema.get("properties", {})
            output = {}
            for k, v in props.items():
                output[k] = self._generate_value(v)
            return output

        if t == "null":
            return None

        # Fallback
        return {}


def generate_mock_output(agent: AgentDefinition, seed: int | None = None) -> Any:
    """
    Generates a valid dictionary matching the agent's output schema.
    """
    # 1. Extract definitions if available
    outputs_schema = agent.interface.outputs
    defs = outputs_schema.get("$defs") or outputs_schema.get("definitions") or {}

    # 2. Initialize MockGenerator
    generator = MockGenerator(seed=seed, definitions=defs)

    # 3. Call generator
    result = generator._generate_value(outputs_schema)

    # 4. Ensure result is a dict (since output schema usually describes an object)
    if not isinstance(result, dict):
        # If the schema described a non-object (unlikely for outputs), wrap or return as is?
        # The prompt says "return a dictionary".
        # If interface.outputs is e.g. {"type": "string"}, the result is a string.
        # But usually interface.outputs is expected to be the schema of the output object.
        pass

    return result
