# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from coreason_manifest.core.common.identity import (
    AgentIdentity,
    DelegationScope,
    SessionContext,
    UserIdentity,
)
from coreason_manifest.core.request import AgentRequest


def test_models_are_frozen() -> None:
    """Ensure that the identity models enforce immutability."""
    agent = AgentIdentity(agent_id="agent-123", version="1.0.0")
    with pytest.raises(ValidationError):
        agent.agent_id = "agent-456"  # type: ignore

    user = UserIdentity(user_id="user-123", roles=["admin"])
    with pytest.raises(ValidationError):
        user.user_id = "user-456"  # type: ignore

    scope = DelegationScope(allowed_tools=["tool-1"])
    with pytest.raises(ValidationError):
        scope.max_budget_usd = 100.0  # type: ignore

    context = SessionContext(
        session_id="session-123",
        user=user,
        agent=agent,
        delegation=scope,
    )
    with pytest.raises(ValidationError):
        context.session_id = "session-456"  # type: ignore


def test_is_authorized_fail_closed_missing_context() -> None:
    """Ensure is_authorized fails-closed when no context is provided but roles are required."""
    request = AgentRequest(
        agent_id="agent-123",
        session_id="session-123",
        inputs={},
    )

    assert request.is_authorized(["admin"]) is False


def test_is_authorized_empty_required_roles() -> None:
    """Ensure is_authorized returns True when no roles are required."""
    request = AgentRequest(
        agent_id="agent-123",
        session_id="session-123",
        inputs={},
    )

    assert request.is_authorized([]) is True


def test_is_authorized_with_roles() -> None:
    """Ensure is_authorized correctly evaluates role intersections."""
    user = UserIdentity(user_id="user-123", roles=["user", "editor"])
    agent = AgentIdentity(agent_id="agent-123", version="1.0.0")
    scope = DelegationScope(allowed_tools=[])
    context = SessionContext(
        session_id="session-123",
        user=user,
        agent=agent,
        delegation=scope,
    )

    request = AgentRequest(
        agent_id="agent-123",
        session_id="session-123",
        inputs={},
        context=context,
    )

    # Exact match
    assert request.is_authorized(["editor"]) is True

    # Intersection match
    assert request.is_authorized(["admin", "user"]) is True

    # No match
    assert request.is_authorized(["admin", "superadmin"]) is False


def test_delegation_scope_budget_serialization() -> None:
    """Ensure DelegationScope max_budget_usd serialization correctly preserves float values."""
    scope = DelegationScope(allowed_tools=[], max_budget_usd=150.50)
    data = scope.model_dump()
    assert data["max_budget_usd"] == 150.50

    # Check JSON serialization
    json_data = json.loads(scope.model_dump_json())
    assert json_data["max_budget_usd"] == 150.50


def test_can_execute_tool() -> None:
    """Ensure can_execute_tool properly checks delegated tool scope."""
    user = UserIdentity(user_id="user-123")
    agent = AgentIdentity(agent_id="agent-123", version="1.0.0")

    # Test strict allowlist
    scope_strict = DelegationScope(allowed_tools=["safe_tool", "read_db"])
    context_strict = SessionContext(session_id="session-123", user=user, agent=agent, delegation=scope_strict)
    request_strict = AgentRequest(agent_id="agent-123", session_id="session-123", inputs={}, context=context_strict)

    assert request_strict.can_execute_tool("safe_tool") is True
    assert request_strict.can_execute_tool("delete_db") is False

    # Test wildcard
    scope_wildcard = DelegationScope(allowed_tools=["*"])
    context_wildcard = SessionContext(session_id="session-123", user=user, agent=agent, delegation=scope_wildcard)
    request_wildcard = AgentRequest(agent_id="agent-123", session_id="session-123", inputs={}, context=context_wildcard)

    assert request_wildcard.can_execute_tool("any_tool") is True

    # Test fail-closed (no context)
    request_no_context = AgentRequest(agent_id="agent-123", session_id="session-123", inputs={})
    assert request_no_context.can_execute_tool("any_tool") is False


def test_session_expiry_aware_datetime() -> None:
    """Ensure session_expiry strictly enforces timezone-aware datetimes."""
    # Aware datetime should succeed
    aware_dt = datetime.now(UTC)
    scope = DelegationScope(allowed_tools=[], session_expiry=aware_dt)
    assert scope.session_expiry == aware_dt

    # Naive datetime should fail validation
    naive_dt = datetime.now()
    with pytest.raises(ValidationError):
        DelegationScope(allowed_tools=[], session_expiry=naive_dt)


def test_w3c_trace_id_serialization() -> None:
    """Ensure SessionContext trace_id serialization preserves the string."""
    user = UserIdentity(user_id="user-123")
    agent = AgentIdentity(agent_id="agent-123", version="1.0.0")
    scope = DelegationScope(allowed_tools=[])

    trace_id_value = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

    context = SessionContext(
        session_id="session-123",
        user=user,
        agent=agent,
        delegation=scope,
        trace_id=trace_id_value,
    )

    data = context.model_dump()
    assert data["trace_id"] == trace_id_value

    # Check JSON serialization
    json_data = json.loads(context.model_dump_json())
    assert json_data["trace_id"] == trace_id_value
