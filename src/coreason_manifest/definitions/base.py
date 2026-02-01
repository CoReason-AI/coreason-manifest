# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class CoReasonBaseModel(BaseModel):
    """Base model for all CoReason Pydantic models with enhanced serialization."""

    model_config = ConfigDict(populate_by_name=True)

    def dump(self, **kwargs: Any) -> Dict[str, Any]:
        """Serialize the model to a JSON-compatible dictionary.

        Uses mode='json' to ensure types like UUID and datetime are serialized to strings.
        Defaults to by_alias=True and exclude_none=True.
        """
        # Set defaults but allow overrides
        kwargs.setdefault("mode", "json")
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
