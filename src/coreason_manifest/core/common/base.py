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

from pydantic import BaseModel, ConfigDict, Field


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

    def __hash__(self) -> int:
        return hash(self.model_dump_canonical())

    def model_dump_canonical(self) -> bytes:
        """Return a strictly sorted, canonical JSON serialization for cryptographic hashing."""
        raw_dict = self.model_dump(mode="json", exclude_none=True, by_alias=True)

        # Architectural Note: Array Sorting Constraints
        def _sort_collections(obj: Any) -> Any:
            """Recursively sorts dictionaries for canonical serialization while explicitly preserving RFC 8785 array ordering."""  # noqa: E501
            if isinstance(obj, dict):
                return {k: _sort_collections(v) for k, v in obj.items()}
            if isinstance(obj, list):
                # Arrays in JSON are strictly ordered (RFC 8785). We must not sort them.
                return [_sort_collections(v) for v in obj]
            return obj

        canonical_dict = _sort_collections(raw_dict)

        return json.dumps(
            canonical_dict,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
