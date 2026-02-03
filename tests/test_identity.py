# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.definitions.identity import Identity


def test_identity_creation() -> None:
    """Test successful creation of an Identity."""
    identity = Identity(id="user-1", name="User One", role="user")
    assert identity.id == "user-1"
    assert identity.name == "User One"
    assert identity.role == "user"


def test_identity_str_representation() -> None:
    """Test the string representation of Identity."""
    identity = Identity(id="agent-007", name="Bond")
    assert str(identity) == "Bond (agent-007)"


def test_identity_anonymous() -> None:
    """Test the anonymous factory method."""
    anon = Identity.anonymous()
    assert anon.id == "anonymous"
    assert anon.name == "Anonymous User"
    assert anon.role == "user"


def test_identity_dump() -> None:
    """Test the dump method inherited from CoReasonBaseModel."""
    identity = Identity(id="test", name="Test")
    data = identity.dump()
    assert data["id"] == "test"
    assert data["name"] == "Test"
