# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CoreasonModel(BaseModel):
    """
    Base class for all domain models in the Coreason Manifest.

    Enforces:
    1. Immutability (frozen=True) - Essential for distributed state consistency.
    2. Strict validation (strict=True) - No silent coercion.
    3. Forbidden extra fields (extra='forbid') - Schema strictness.
    4. Deterministic serialization - Keys are sorted for hash consistency.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        populate_by_name=True,  # Allow using field names or aliases
    )

    # Storage for unknown fields caught by the funnel
    annotations: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _funnel_unknown_fields(cls, data: Any) -> Any:
        """Intercepts the raw dict before instantiation to funnel unknown keys safely."""
        if isinstance(data, dict):
            # Architectural Note: Must account for both field names AND aliases
            known_keys = set()
            for name, field in cls.model_fields.items():
                known_keys.add(name)
                if field.alias:
                    known_keys.add(field.alias)
                # Account for complex validation aliases
                if field.validation_alias:
                    if isinstance(field.validation_alias, str):
                        known_keys.add(field.validation_alias)
                    elif hasattr(field.validation_alias, "choices"):
                        for choice in getattr(field.validation_alias, "choices", []):
                            if isinstance(choice, str):
                                known_keys.add(choice)

            annotations = data.get("annotations", {})
            keys_to_remove = []

            for key, value in data.items():
                if key not in known_keys and key != "annotations":
                    annotations[key] = value
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del data[key]

            if annotations:
                data["annotations"] = annotations

        return data

    def model_dump_json(self, **kwargs: Any) -> str:
        """
        Overrides the default JSON dump to enforce deterministic output.
        We serialize to a dict first, then use json.dumps with sort_keys=True.
        """
        # Extract json.dumps specific arguments
        indent = kwargs.pop("indent", None)

        # Ensure round_trip is True unless explicitly overridden (which we discourage)
        if "round_trip" not in kwargs:
            kwargs["round_trip"] = True

        # Dump to python dict first
        # We pass remaining kwargs (like include, exclude, by_alias) to model_dump
        data = self.model_dump(mode="json", **kwargs)

        # Use json.dumps to ensure key sorting
        return json.dumps(data, sort_keys=True, ensure_ascii=False, indent=indent)

    def model_dump_canonical(self) -> bytes:
        """RFC-8785 strict canonical serialization for cryptographic hashing."""
        raw_dict = self.model_dump(mode="json", exclude_none=True, by_alias=True)

        # Architectural Note: Recursively sort lists to prevent non-deterministic set-to-list casting
        def _sort_collections(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _sort_collections(v) for k, v in obj.items()}
            if isinstance(obj, list):
                # Try to sort, fallback to original if elements are unorderable dicts
                try:
                    return sorted(_sort_collections(v) for v in obj)
                except TypeError:
                    return [_sort_collections(v) for v in obj]
            return obj

        canonical_dict = _sort_collections(raw_dict)

        return json.dumps(
            canonical_dict,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
