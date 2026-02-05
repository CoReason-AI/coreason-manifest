# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import Enum
from typing import Annotated, Any

from pydantic import AnyUrl, BaseModel, ConfigDict, PlainSerializer


class CoReasonBaseModel(BaseModel):
    """Base model for all CoReason Pydantic models with enhanced serialization.

    This base class addresses JSON serialization challenges in Pydantic v2 (e.g., UUID, datetime)
    by providing standardized methods (`dump`, `to_json`) with optimal configuration.

    For a detailed rationale, see `docs/coreason_base_model_rationale.md`.
    """

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    def dump(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize the model to a JSON-compatible dictionary.

        Uses mode='json' to ensure types like UUID and datetime are serialized to strings.
        Defaults to by_alias=True and exclude_none=True.
        """
        # Strict enforcement of json mode for zero-friction serialization
        kwargs["mode"] = "json"
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", True)
        return self.model_dump(**kwargs)

    def to_json(self, **kwargs: Any) -> str:
        """Serialize the model to a JSON string.

        Defaults to by_alias=True and exclude_none=True.
        """
        # Set defaults but allow overrides
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", True)
        return self.model_dump_json(**kwargs)


# Strict URI type that serializes to string
StrictUri = Annotated[
    AnyUrl,
    PlainSerializer(lambda x: str(x), return_type=str),
]


class ToolRiskLevel(str, Enum):
    """Risk level for the tool."""

    SAFE = "safe"
    STANDARD = "standard"
    CRITICAL = "critical"
