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
from pydantic import TypeAdapter, ValidationError

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
    data = ident.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert data == {"id": "agent-007", "name": "Bond", "role": "agent"}

    # Test without optional field
    ident2 = Identity(id="u1", name="U1")
    data2 = ident2.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert data2 == {"id": "u1", "name": "U1"}


# --- Edge Case Tests ---


def test_identity_edge_cases_empty() -> None:
    """Test empty strings."""
    ident = Identity(id="", name="")
    assert ident.id == ""
    assert ident.name == ""
    assert str(ident) == " ()"


def test_identity_edge_cases_special_chars() -> None:
    """Test special characters and Unicode."""
    ident = Identity(id="!@#$", name="U∫er ☃")
    assert ident.id == "!@#$"
    assert ident.name == "U∫er ☃"
    assert str(ident) == "U∫er ☃ (!@#$)"


def test_identity_explicit_none() -> None:
    """Test explicitly passing None for optional role."""
    ident = Identity(id="x", name="X", role=None)
    assert ident.role is None
    data = ident.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert "role" not in data  # dump defaults to exclude_none=True


def test_identity_type_validation() -> None:
    """Test strict type validation triggers (Pydantic coercions or errors)."""
    # Pydantic V2 often coerces simple types by default unless Strict is used.
    # But passing an object that can't be coerced to string should fail.
    with pytest.raises(ValidationError):
        Identity(id={}, name="Test")


# --- Complex Case Tests ---


def test_identity_equality() -> None:
    """Test equality and inequality."""
    i1 = Identity(id="a", name="A")
    i2 = Identity(id="a", name="A")
    i3 = Identity(id="b", name="B")

    assert i1 == i2
    assert i1 != i3
    assert i1 != "some string"  # type: ignore[comparison-overlap]


def test_identity_hashing() -> None:
    """Test that Identity is hashable and works in sets."""
    i1 = Identity(id="a", name="A")
    i2 = Identity(id="a", name="A")
    i3 = Identity(id="b", name="B")

    s = {i1, i2, i3}
    assert len(s) == 2
    assert i1 in s
    assert i3 in s


def test_identity_list_serialization() -> None:
    """Test serialization of a list of identities using TypeAdapter."""
    ids = [Identity(id="1", name="One"), Identity(id="2", name="Two", role="test")]

    adapter = TypeAdapter(list[Identity])
    # Pydantic's dump_python works like model_dump but for adapters
    data = adapter.dump_python(ids, mode="json", exclude_none=True)

    assert len(data) == 2
    assert data[0] == {"id": "1", "name": "One"}
    assert data[1] == {"id": "2", "name": "Two", "role": "test"}


def test_identity_copy() -> None:
    """Test model_copy behavior."""
    i1 = Identity(id="orig", name="Original", role="old")
    # model_copy does shallow copy. With update, it creates new instance.
    i2 = i1.model_copy(update={"name": "Copy"})

    assert i1.name == "Original"
    assert i2.name == "Copy"
    assert i2.id == "orig"
    assert i2.role == "old"

    # Ensure copy is also frozen
    with pytest.raises(ValidationError):
        i2.role = "new"  # type: ignore[misc]
