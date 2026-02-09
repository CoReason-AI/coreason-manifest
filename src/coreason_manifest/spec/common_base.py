# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import hashlib
import json
from enum import StrEnum
from typing import Annotated

from pydantic import AnyUrl, BaseModel, ConfigDict, PlainSerializer


class ManifestBaseModel(BaseModel):
    """Base model for all CoReason Pydantic models with enhanced serialization.

    This base class addresses JSON serialization challenges in Pydantic v2 (e.g., UUID, datetime)
    by providing standardized methods (`dump`, `to_json`) with optimal configuration.

    For a detailed rationale, see `docs/coreason_base_model_rationale.md`.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        frozen=True,
        ser_json_timedelta="float",
        ser_json_bytes="utf8",
    )

    def compute_hash(self, exclude: set[str] | None = None) -> str:
        """
        Compute a deterministic SHA-256 hash of the model.

        Args:
            exclude: A set of field names to exclude from the hash.
                     Useful for excluding self-referential hashes or timestamps.

        Returns:
            The SHA-256 hex digest of the canonical JSON representation.
        """
        # 1. Get dictionary via self.model_dump()
        # Use mode='json' to ensure types like UUID and datetime are serialized to strings.
        # Defaults to by_alias=True and exclude_none=True.
        data = self.model_dump(mode="json", by_alias=True, exclude_none=True)

        # 2. If exclude provided, remove keys from dict
        if exclude:
            for field in exclude:
                data.pop(field, None)

        # 3. Dump to JSON string (sort_keys=True, ensure_ascii=False)
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)

        # 4. Encode to bytes (utf-8)
        json_bytes = json_str.encode("utf-8")

        # 5. Return hashlib.sha256(...).hexdigest()
        return hashlib.sha256(json_bytes).hexdigest()


# Strict URI type that serializes to string
StrictUri = Annotated[
    AnyUrl,
    PlainSerializer(lambda x: str(x), return_type=str),
]


class ToolRiskLevel(StrEnum):
    """Risk level for the tool."""

    SAFE = "safe"
    STANDARD = "standard"
    CRITICAL = "critical"
