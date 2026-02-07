# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import ConfigDict, Field, model_validator

from coreason_manifest.spec.common_base import CoReasonBaseModel


class AgentRequest(CoReasonBaseModel):
    """Transport Envelope for all communication within the CoReason ecosystem.

    Ensures strict validation of trace lineage and context propagation.
    """

    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    root_request_id: UUID | None = None
    parent_request_id: UUID | None = None
    payload: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="before")
    @classmethod
    def validate_lineage(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 1. Ensure request_id is present (needed for auto-rooting reference)
            if "request_id" not in data or data["request_id"] is None:
                data["request_id"] = uuid4()

            req_id = data["request_id"]
            parent_id = data.get("parent_request_id")
            root_id = data.get("root_request_id")

            # 2. Lineage Enforcement
            if parent_id is not None and root_id is None:
                raise ValueError("Broken Trace: parent_request_id provided without root_request_id.")

            # 3. Auto-Rooting
            if root_id is None:
                data["root_request_id"] = req_id

        return data

    def create_child(self, payload: dict[str, Any], **kwargs: Any) -> "AgentRequest":
        """Create a child request that preserves trace context."""
        return AgentRequest(
            session_id=self.session_id,
            root_request_id=self.root_request_id,
            parent_request_id=self.request_id,
            payload=payload,
            **kwargs
        )
