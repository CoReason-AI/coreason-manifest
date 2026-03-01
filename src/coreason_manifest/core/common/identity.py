# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from pydantic import AwareDatetime, ConfigDict, Field

from coreason_manifest.core.common_base import CoreasonModel


class AgentIdentity(CoreasonModel):
    model_config = ConfigDict(frozen=True)
    """
    Cryptographic identity of the agent operating within the Zero-Trust Prompt paradigm.
    Proves the acting software entity.
    """

    agent_id: str = Field(..., description="Unique, verifiable ID for the agent instance.")
    version: str = Field(..., description="Version of the agent.")
    software_hash: str | None = Field(None, description="Cryptographic hash of the agent's manifest definition.")


class UserIdentity(CoreasonModel):
    model_config = ConfigDict(frozen=True)
    """
    The principal human or service account initiating the trace in the On-Behalf-Of (OBO) flow.
    Includes Persona-Based Access Control (PBAC) roles.
    """

    user_id: str = Field(..., description="The principal human or service account initiating the trace.")
    roles: list[str] = Field(
        default_factory=list, description="Persona-Based Access Control (PBAC) roles assigned to the user."
    )


class DelegationScope(CoreasonModel):
    model_config = ConfigDict(frozen=True)
    """
    The strict boundaries of authority granted to the agent for this specific trace.
    Part of the Zero-Trust Identity Context Envelope.
    """

    allowed_tools: list[str] = Field(
        default_factory=list, description="Strictly scoped tool whitelist for this specific request."
    )
    max_budget_usd: float | None = Field(None, description="Financial cap for this trace.")
    session_expiry: AwareDatetime | None = Field(
        None, description="When this context envelope expires. Must be TZ-aware."
    )


class SessionContext(CoreasonModel):
    model_config = ConfigDict(frozen=True)
    """
    The Zero-Trust Identity Context Envelope for this request.
    Proves cryptographically who is making the request, who the agent is, and what its delegated authority is.
    """

    session_id: str = Field(..., description="ID of the interaction session.")
    user: UserIdentity = Field(..., description="The delegating principal.")
    agent: AgentIdentity = Field(..., description="The acting agent.")
    delegation: DelegationScope = Field(..., description="The authority granted.")
    trace_id: str | None = Field(
        None,
        pattern=r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$",
        description="W3C Trace Context ID for distributed secure tracking.",
    )
