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

from pydantic import BaseModel, ConfigDict


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
