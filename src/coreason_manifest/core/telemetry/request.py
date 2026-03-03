from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from coreason_manifest.core.common.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.core.common.identity import IdentityPassport
from coreason_manifest.core.workflow.exceptions import LineageIntegrityError
from coreason_manifest.core.workflow.flow import GraphFlow, LinearFlow


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
    hash_version: Literal["v2"] = Field(default="v2", description="Versioning for integrity strategies.")

    # Execution Manifest
    manifest: GraphFlow | LinearFlow = Field(..., description="The AOT-compiled execution graph.")

    # V2 Standard: The Zero-Trust Identity Envelope.
    # Strictly bound to IdentityPassport post-merge.
    passport: IdentityPassport | None = Field(
        None, description="The cryptographic Zero-Trust Identity Passport for this request."
    )

    @model_validator(mode="before")
    @classmethod
    def enforce_lineage_rooting(cls, data: Any) -> Any:
        """Promote current request_id to root_request_id if no root and parent exist."""
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

        return data

    @model_validator(mode="after")
    def validate_trace_integrity(self) -> "AgentRequest":
        """Enforce strict trace integrity and lineage validity.

        Raises:
            ManifestError: If lineage integrity is broken."""
        errors = []

        # Rule 1: Orphaned trace check (Parent exists, but Root missing)
        if self.parent_request_id and not self.root_request_id:
            # Architectural Note: Structured Exception Contracts
            err = LineageIntegrityError("Broken Lineage: Orphaned request (parent set, root missing).")
            err.add_note(f"Request ID: {self.request_id}")
            err.add_note(f"Parent Request ID: {self.parent_request_id}")
            errors.append(err)

        # Rule 2: Root Consistency (If root == self, parent must be None)
        # This prevents cyclic root references where root points to self but parent is someone else (contradiction)
        if self.root_request_id == self.request_id and self.parent_request_id is not None:
            err = LineageIntegrityError("Broken Lineage: Root request cannot imply a parent.")
            err.add_note(f"Request ID: {self.request_id}")
            err.add_note(f"Parent Request ID: {self.parent_request_id}")
            errors.append(err)

        # Rule 3: Self-Parenting Cycle
        if self.parent_request_id and self.parent_request_id == self.request_id:
            err = LineageIntegrityError("Broken Lineage: Self-referential parent_request_id detected.")
            err.add_note(f"Request ID: {self.request_id}")
            errors.append(err)

        if errors:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.SEC_LINEAGE_001,
                message="Multiple Trace Integrity Violations detected.",
                context={"violations": [str(e) for e in errors]},
            )

        return self
