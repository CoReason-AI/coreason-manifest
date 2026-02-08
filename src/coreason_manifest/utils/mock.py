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
import secrets
import string
import uuid
from datetime import UTC, datetime
from typing import Any, cast

from coreason_manifest.spec.v2.definitions import AgentDefinition

type JsonValue = dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None
type JsonSchema = dict[str, Any]


class MockGenerator:
    def __init__(
        self,
        seed: int | None = None,
        definitions: JsonSchema | None = None,
        strict: bool = False,
    ):
        # Use secrets.SystemRandom for cryptographic strength by default.
        # Fallback to random.Random only if a seed is explicitly provided for determinism.
        if seed is not None:
            self.rng = random.Random(seed)
        else:
            self.rng = secrets.SystemRandom()

        self.definitions = definitions or {}
        self.recursion_depth = 0
        self.max_depth = 10
        self.strict = strict

    def _random_string(self, min_len: int = 5, max_len: int = 20) -> str:
        length = self.rng.randint(min_len, max_len)
        return "".join(self.rng.choices(string.ascii_letters + string.digits, k=length))

    def _random_int(self, min_val: int = 0, max_val: int = 100) -> int:
        return self.rng.randint(min_val, max_val)

    def _random_bool(self) -> bool:
        return self.rng.choice([True, False])

    def _get_safe_default(self, schema: JsonSchema) -> JsonValue:
        """Returns a safe default value based on the schema type."""
        t = schema.get("type")

        # Handle union types (prioritize non-null)
        if isinstance(t, list):
            non_null = [x for x in t if x != "null"]
            t = non_null[0] if non_null else "object"

        if t == "string":
            return ""
        if t == "integer":
            return 0
        if t == "number":
            return 0.0
        if t == "boolean":
            return False
        if t == "array":
            return []
        if t == "object":
            return {}
        if t == "null":
            return None

        # Fallback
        if self.strict:
            raise ValueError(f"Cannot determine safe default for schema: {schema}")
        return {}

    def _deep_merge(self, base: JsonSchema, update: JsonSchema) -> JsonSchema:
        """Deep merge two schemas."""
        merged = base.copy()
        for k, v in update.items():
            if (
                k == "properties"
                and isinstance(v, dict)
                and "properties" in merged
                and isinstance(merged["properties"], dict)
            ):
                merged["properties"] = self._deep_merge(merged["properties"], v)
            elif (
                k == "required"
                and isinstance(v, list)
                and "required" in merged
                and isinstance(merged["required"], list)
            ):
                merged["required"] = list(set(merged["required"] + v))
            elif isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
                merged[k] = self._deep_merge(merged[k], v)
            else:
                merged[k] = v
        return merged

    def _resolve_ref(self, ref: str) -> JsonSchema:
        ref_name = ref.split("/")[-1]
        if ref_name in self.definitions:
            return cast("JsonSchema", self.definitions[ref_name])
        if self.strict:
            raise ValueError(f"Missing definition for reference: {ref}")
        return {}

    def _generate_value(self, schema: JsonSchema) -> JsonValue:
        if self.recursion_depth > self.max_depth:
            return self._get_safe_default(schema)

        # Handle $ref
        if "$ref" in schema:
            self.recursion_depth += 1
            try:
                ref_schema = self._resolve_ref(schema["$ref"])
                return self._generate_value(ref_schema)
            finally:
                self.recursion_depth -= 1

        # Handle enum
        if "enum" in schema:
            return cast("JsonValue", self.rng.choice(schema["enum"]))

        # Handle const
        if "const" in schema:
            return cast("JsonValue", schema["const"])

        # Handle composite keywords (allOf)
        if "allOf" in schema:
            merged: JsonSchema = {}
            for s in schema["allOf"]:
                sub_schema = s
                if "$ref" in s:
                    sub_schema = self._resolve_ref(s["$ref"])
                merged = self._deep_merge(merged, sub_schema)

            # Merge the original schema into it (except allOf)
            combined = merged.copy()
            for k, v in schema.items():
                if k != "allOf":
                    if k == "properties" and isinstance(v, dict) and "properties" in combined:
                        combined["properties"] = self._deep_merge(combined["properties"], v)
                    else:
                        combined[k] = v

            self.recursion_depth += 1
            try:
                return self._generate_value(combined)
            finally:
                self.recursion_depth -= 1

        # Handle anyOf / oneOf
        if "anyOf" in schema or "oneOf" in schema:
            options = schema.get("anyOf") or schema.get("oneOf")
            if options:
                choice = self.rng.choice(options)
                return self._generate_value(choice)

        t = schema.get("type")

        # Handle union types
        if isinstance(t, list):
            non_null = [x for x in t if x != "null"]
            if non_null:
                t = self.rng.choice(non_null)
            else:
                return None

        if t is None:
            # Heuristics for missing type
            if "properties" in schema:
                t = "object"
            elif "items" in schema:
                t = "array"

        if t == "string":
            return self._generate_string(schema)
        if t == "integer":
            return self._generate_int(schema)
        if t == "number":
            return self._generate_float(schema)
        if t == "boolean":
            return self._generate_bool(schema)
        if t == "array":
            return self._generate_array(schema)
        if t == "object":
            return self._generate_object(schema)
        if t == "null":
            return None

        # Fallback
        if self.strict:
            raise ValueError(f"Unknown type: {t} in schema: {schema}")
        return {}

    def _generate_string(self, schema: JsonSchema) -> str:
        fmt = schema.get("format")
        if fmt == "date-time":
            ts = self.rng.randint(1600000000, 1700000000)
            dt = datetime.fromtimestamp(ts, tz=UTC)
            return dt.isoformat().replace("+00:00", "Z")
        if fmt == "uuid":
            return str(uuid.UUID(int=self.rng.getrandbits(128)))

        min_len = schema.get("minLength", 5)
        max_len = schema.get("maxLength", 20)

        if max_len < min_len:
            max_len = min_len + 10

        return self._random_string(min_len, max_len)

    def _generate_int(self, schema: JsonSchema) -> int:
        min_val = schema.get("minimum", 0)
        max_val = schema.get("maximum", 100)

        if max_val < min_val:
            max_val = min_val + 100

        return self._random_int(min_val, max_val)

    def _generate_float(self, schema: JsonSchema) -> float:
        min_val = schema.get("minimum", 0.0)
        max_val = schema.get("maximum", 100.0)

        if max_val < min_val:
            max_val = min_val + 100.0

        return self.rng.uniform(min_val, max_val)

    def _generate_bool(self, _schema: JsonSchema) -> bool:
        return self._random_bool()

    def _generate_array(self, schema: JsonSchema) -> list[JsonValue]:
        items_schema = schema.get("items", {})
        min_items = schema.get("minItems", 1)
        max_items = schema.get("maxItems", 3)
        length = self.rng.randint(min_items, max_items)
        return [self._generate_value(items_schema) for _ in range(length)]

    def _generate_object(self, schema: JsonSchema) -> dict[str, JsonValue]:
        props = schema.get("properties", {})
        output = {}
        for k, v in props.items():
            output[k] = self._generate_value(v)

        # Handle additionalProperties if strict?
        # For now, just properties is fine.
        return output


def generate_mock_output(agent: AgentDefinition, seed: int | None = None, strict: bool = False) -> JsonValue:
    """
    Generates a valid dictionary matching the agent's output schema.
    """
    outputs_schema = agent.interface.outputs
    defs = outputs_schema.get("$defs") or outputs_schema.get("definitions") or {}

    generator = MockGenerator(seed=seed, definitions=defs, strict=strict)
    return generator._generate_value(outputs_schema)
