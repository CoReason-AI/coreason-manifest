# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest import Identity


def test_identity_initialization() -> None:
    """Test proper initialization of Identity."""
    ident = Identity(id="agent-007", name="Bond", role="agent")
    assert ident.id == "agent-007"
    assert ident.name == "Bond"
    assert ident.role == "agent"


def test_identity_defaults() -> None:
    """Test defaults (role is Optional)."""
    ident = Identity(id="user-123", name="Alice")
    assert ident.id == "user-123"
    assert ident.name == "Alice"
    assert ident.role is None


def test_identity_immutability() -> None:
    """Test that Identity is frozen."""
    ident = Identity(id="test", name="Test")
    with pytest.raises(ValidationError):
        ident.name = "New Name"  # type: ignore[misc]


def test_identity_str_representation() -> None:
    """Test the __str__ method."""
    ident = Identity(id="agent-007", name="Bond")
    assert str(ident) == "Bond (agent-007)"


def test_identity_anonymous_factory() -> None:
    """Test the anonymous factory method."""
    anon = Identity.anonymous()
    assert anon.id == "anonymous"
    assert anon.name == "Anonymous User"
    assert anon.role == "user"


def test_identity_serialization() -> None:
    """Test serialization via dump()."""
    ident = Identity(id="agent-007", name="Bond", role="agent")
    data = ident.dump()
    assert data == {"id": "agent-007", "name": "Bond", "role": "agent"}

    # Test without optional field
    ident2 = Identity(id="u1", name="U1")
    data2 = ident2.dump()
    assert data2 == {"id": "u1", "name": "U1"}
