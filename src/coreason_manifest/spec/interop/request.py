from typing import Any, Literal, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentRequest(BaseModel):
    """
    Standard envelope for agent interaction requests.
    Enforces W3C Trace Context and strict lineage.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    parent_request_id: str | None = None
    root_request_id: str | None = None

    # W3C Trace Context
    traceparent: str | None = Field(
        default=None,
        pattern=r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$",
        description="W3C Trace Context: traceparent header",
    )
    tracestate: str | None = Field(default=None, description="W3C Trace Context: tracestate header")

    # Payload
    agent_id: str
    session_id: str
    inputs: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Versioning
    hash_version: Literal["v1"] = Field(default="v1", description="Versioning for integrity strategies.")

    def create_child(self, metadata: dict[str, Any]) -> Self:
        return self.model_copy(
            update={
                "request_id": str(uuid4()),
                "parent_request_id": self.request_id,
                "metadata": metadata,
            }
        )

    @model_validator(mode="before")
    @classmethod
    def enforce_lineage_rooting(cls, data: Any) -> Any:
        """
        Auto-Rooting: If no root is provided and no parent exists,
        promote current request_id to root_request_id.
        """
        if isinstance(data, dict):
            # COPY data to avoid side effects on the input dict
            data = data.copy()

            req_id = data.get("request_id")
            parent = data.get("parent_request_id")
            root = data.get("root_request_id")

            # If request_id is not provided, we can't auto-root reliably here if we rely on default_factory.
            # But typically requests are created with an ID.
            # If not, Pydantic will generate it later, but we need it for root.
            # So if missing, generate it now.
            if not req_id:
                req_id = str(uuid4())
                data["request_id"] = req_id

            # Case 1: No parent, no root -> New Root
            if not parent and not root:
                data["root_request_id"] = req_id

            # Case 2: Parent exists, but no root -> Error (handled by after validator or strictly here)
            # The prompt says "Strictly assert...". We'll let the 'after' validator handle the error checks
            # to be cleaner, or checking here.
            # However, if parent is present, we cannot auto-guess the root. It MUST be provided.

        return data

    @model_validator(mode="after")
    def validate_trace_integrity(self) -> "AgentRequest":
        """
        Enforces strict lineage integrity.
        """
        # Rule: Orphaned trace check
        if self.parent_request_id and not self.root_request_id:
            raise ValueError("Broken Lineage: parent_request_id is set but root_request_id is missing.")

        # W3C consistency (Optional but good):
        # If traceparent is present, it should ideally align with IDs,
        # but we treat them as separate opaque identifiers for now as per prompt instructions
        # focusing on the specific validation rule.

        return self
