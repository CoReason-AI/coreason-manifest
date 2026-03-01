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
    """
    Cryptographic identity of the agent operating within the Zero-Trust Prompt paradigm.
    Proves the acting software entity.
    """

    model_config = ConfigDict(frozen=True)

    agent_id: str = Field(..., description="Unique, verifiable ID for the agent instance.", examples=["agent_alpha_01"])
    version: str = Field(..., description="Version of the agent.", examples=["1.2.0"])
    software_hash: str | None = Field(
        None,
        description="Cryptographic hash of the agent's manifest definition.",
        examples=["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
    )


class UserIdentity(CoreasonModel):
    """
    The principal human or service account initiating the trace in the On-Behalf-Of (OBO) flow.
    Includes Persona-Based Access Control (PBAC) roles.
    """

    model_config = ConfigDict(frozen=True)

    user_id: str = Field(
        ..., description="The principal human or service account initiating the trace.", examples=["user_789"]
    )
    roles: list[str] = Field(
        default_factory=list,
        description="Persona-Based Access Control (PBAC) roles assigned to the user.",
        examples=[["admin", "reviewer"]],
    )


class DelegationScope(CoreasonModel):
    """
    The strict boundaries of authority granted to the agent for this specific trace.
    Part of the Zero-Trust Identity Context Envelope.
    """

    model_config = ConfigDict(frozen=True)

    allowed_tools: list[str] = Field(
        default_factory=list,
        description="Strictly scoped tool whitelist for this specific request.",
        examples=[["search_tool", "calculator_tool"]],
    )
    max_budget_usd: float | None = Field(None, description="Financial cap for this trace.", examples=[10.00])
    session_expiry: AwareDatetime | None = Field(
        None, description="When this context envelope expires. Must be TZ-aware.", examples=["2025-01-01T12:00:00Z"]
    )


class SessionContext(CoreasonModel):
    """
    The Zero-Trust Identity Context Envelope for this request.
    Proves cryptographically who is making the request, who the agent is, and what its delegated authority is.
    """

    model_config = ConfigDict(frozen=True)

    session_id: str = Field(..., description="ID of the interaction session.", examples=["sess_001"])
    user: UserIdentity = Field(
        ..., description="The delegating principal.", examples=[{"user_id": "user_789", "roles": ["admin"]}]
    )
    agent: AgentIdentity = Field(
        ...,
        description="The acting agent.",
        examples=[
            {
                "agent_id": "agent_alpha_01",
                "version": "1.2.0",
                "software_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            }
        ],
    )
    delegation: DelegationScope = Field(
        ...,
        description="The authority granted.",
        examples=[{"allowed_tools": ["search_tool"], "max_budget_usd": 5.0, "session_expiry": "2025-01-01T12:00:00Z"}],
    )
    trace_id: str | None = Field(
        None,
        pattern=r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$",
        description="W3C Trace Context ID for distributed secure tracking.",
        examples=["00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"],
    )
