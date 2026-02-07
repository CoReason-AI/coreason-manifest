# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any
from uuid import UUID, uuid4

from pydantic import ConfigDict, Field, model_validator

from ..common_base import CoReasonBaseModel


class AgentRequest(CoReasonBaseModel):
    """Strictly typed payload inside a ServiceRequest."""

    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(default_factory=uuid4)
    root_request_id: UUID | None = Field(
        default=None, description="The ID of the original user request. Must always be present."
    )
    parent_request_id: UUID | None = Field(default=None, description="The ID of the immediate caller.")

    query: str
    files: list[str] = Field(default_factory=list)
    conversation_id: str | None = None
    session_id: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def enforce_lineage(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Ensure request_id is present (needed for auto-rooting)
            if "request_id" not in data:
                data["request_id"] = uuid4()

            # Check for Broken Chain FIRST
            if data.get("parent_request_id") is not None and data.get("root_request_id") is None:
                raise ValueError("Broken Lineage: 'root_request_id' is required when 'parent_request_id' is present.")

            # Auto-rooting (Only if no parent)
            if data.get("root_request_id") is None:
                data["root_request_id"] = data["request_id"]
        return data
