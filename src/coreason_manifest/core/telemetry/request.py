from typing import Any, Literal, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from coreason_manifest.core.common.identity import SessionContext
from coreason_manifest.core.exceptions import LineageIntegrityError, ManifestError, ManifestErrorCode
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

    # Context Envelope
    context: SessionContext | None = Field(
        None, description="The Zero-Trust Identity Context Envelope for this request."
    )

    # SOTA 2026: The Zero-Trust Identity Envelope.
    # Typed as Any during parallel development; will be strictly bound to IdentityPassport post-merge.
    passport: Any | None = Field(None, description="The cryptographic Zero-Trust Identity Passport for this request.")

    def verify_passport_authorization(self, required_roles: list[str]) -> bool:
        """
        Safely checks if the passport's PBAC roles intersect with the required roles.
        Fails closed (returns False) if the passport or roles are missing.
        """
        if not required_roles:
            return True
        if not self.passport:
            return False

        # Duck-typing access for parallel development phase
        user_context = (
            getattr(self.passport, "user", {}) if not isinstance(self.passport, dict) else self.passport.get("user", {})
        )
        user_roles = set(
            getattr(user_context, "roles", []) if not isinstance(user_context, dict) else user_context.get("roles", [])
        )

        return any(role in user_roles for role in required_roles)

    def verify_tool_delegation(self, tool_name: str, current_timestamp: float) -> bool:
        """
        SOTA 2026: Time-bound, Caveat-aware capability verification.
        Evaluates the tool request against the passport's temporal bounds and whitelists.
        Requires current_timestamp to be passed in to maintain functional purity.
        """
        if not self.passport:
            return False

        delegation = (
            getattr(self.passport, "delegation", {})
            if not isinstance(self.passport, dict)
            else self.passport.get("delegation", {})
        )
        if not delegation:
            return False

        # 1. Temporal Bounding (Fail Closed if Expired)
        expires_at = (
            getattr(delegation, "expires_at", 0.0)
            if not isinstance(delegation, dict)
            else delegation.get("expires_at", 0.0)
        )
        if current_timestamp > expires_at:
            return False

        # 2. Strict Tool Whitelist Check
        allowed_tools = (
            getattr(delegation, "allowed_tools", [])
            if not isinstance(delegation, dict)
            else delegation.get("allowed_tools", [])
        )
        return not ("*" not in allowed_tools and tool_name not in allowed_tools)

    def is_authorized(self, required_roles: list[str]) -> bool:
        """
        Safely checks if the user's PBAC roles intersect with the required roles.
        If context is missing and roles are required, this fails closed (returns False).
        """
        if not required_roles:
            return True
        if self.context is None:
            return False

        # Check for intersection of required roles with user's roles
        user_roles = set(self.context.user.roles)
        return any(role in user_roles for role in required_roles)

    def can_execute_tool(self, tool_name: str) -> bool:
        """
        Safely checks if the requested tool is within the agent's strictly delegated scope.
        Fails closed if the context or delegation scope is missing.
        """
        if self.context is None or self.context.delegation is None:
            return False

        # SOTA Pattern: Support explicit wildcard delegation or exact match
        allowed = self.context.delegation.allowed_tools
        if "*" in allowed:
            return True

        return tool_name in allowed

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
