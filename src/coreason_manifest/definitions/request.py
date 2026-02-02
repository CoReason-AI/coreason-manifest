from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import ConfigDict, Field, model_validator

from coreason_manifest.definitions.base import CoReasonBaseModel


class AgentRequest(CoReasonBaseModel):
    """Standard envelope for Agent invocations with distributed tracing support.

    Wraps every agent invocation to automatically propagate trace context
    (Root ID -> Parent ID -> Child ID), enabling visualization in tools like Jaeger.
    """

    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(default_factory=uuid4, description="Unique identifier for this specific request")
    session_id: UUID = Field(..., description="The conversation/session ID this request belongs to")
    root_request_id: Optional[UUID] = Field(default=None, description="The ID of the first request in the causal chain")
    parent_request_id: Optional[UUID] = Field(default=None, description="The ID of the request that triggered this one")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(..., description="The actual input arguments for the agent")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary headers or context (e.g., user locale)"
    )

    @model_validator(mode="after")
    def validate_tracing_ids(self) -> "AgentRequest":
        # Logic to ensure root_request_id is populated
        if self.root_request_id is None:
            # If no parent, I am the root.
            if self.parent_request_id is None:
                self.__dict__["root_request_id"] = self.request_id
            else:
                raise ValueError("Root ID missing while Parent ID is present.")
        return self
