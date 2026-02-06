# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

from coreason_manifest import Identity, SessionHandle
from coreason_manifest.spec.common.session import Interaction


class MockSession:
    """A mock session that implements the SessionHandle protocol."""

    @property
    def session_id(self) -> str:
        return "sess_123"

    @property
    def identity(self) -> Identity:
        return Identity(id="user_123", name="Test User")

    async def history(self, limit: int = 10, offset: int = 0) -> list[Interaction]:
        _ = (limit, offset)  # Suppress unused argument warning
        return []

    async def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> list[str]:
        _ = (query, limit, threshold)  # Suppress unused argument warning
        return ["fact1"]

    async def store(self, key: str, value: Any) -> None:
        _ = (key, value)  # Suppress unused argument warning

    async def get(self, key: str, default: Any = None) -> Any:
        _ = key  # Suppress unused argument warning
        return default


class IncompleteSession:
    """A mock session that fails to implement the SessionHandle protocol."""

    @property
    def session_id(self) -> str:
        return "sess_456"

    @property
    def identity(self) -> Identity:
        return Identity(id="user_456", name="Test User 2")

    async def history(self, limit: int = 10, offset: int = 0) -> list[Interaction]:
        _ = (limit, offset)  # Suppress unused argument warning
        return []

    # Missing recall

    async def store(self, key: str, value: Any) -> None:
        _ = (key, value)  # Suppress unused argument warning

    async def get(self, key: str, default: Any = None) -> Any:
        _ = key  # Suppress unused argument warning
        return default


class SyncSession:
    """
    A mock session that implements methods synchronously.

    WARNING: This theoretically fails Protocol compliance at runtime if checked strictly for 'async'
    but `typing.Protocol` with `@runtime_checkable` usually just checks for method presence,
    not whether they are coroutines.
    """

    @property
    def session_id(self) -> str:
        return "sess_sync"

    @property
    def identity(self) -> Identity:
        return Identity(id="user_sync", name="Sync User")

    def history(self, limit: int = 10, offset: int = 0) -> list[Interaction]:
        _ = (limit, offset)
        return []

    def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> list[str]:
        _ = (query, limit, threshold)
        return []

    def store(self, key: str, value: Any) -> None:
        _ = (key, value)

    def get(self, key: str, default: Any = None) -> Any:
        _ = key
        return default


class MissingPropertySession:
    """Missing the identity property."""

    @property
    def session_id(self) -> str:
        return "sess_missing_prop"

    async def history(self, limit: int = 10, offset: int = 0) -> list[Interaction]:
        _ = (limit, offset)
        return []

    async def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> list[str]:
        _ = (query, limit, threshold)
        return []

    async def store(self, key: str, value: Any) -> None:
        _ = (key, value)

    async def get(self, key: str, default: Any = None) -> Any:
        _ = key
        return default


# --- Complex Inheritance Cases ---

class BaseSession:
    """Base class providing common functionality."""
    @property
    def session_id(self) -> str:
        return "sess_base"

    @property
    def identity(self) -> Identity:
        return Identity(id="base", name="Base")


class StorageMixin:
    """Mixin providing storage capabilities."""
    async def store(self, key: str, value: Any) -> None:
        _ = (key, value)

    async def get(self, key: str, default: Any = None) -> Any:
        _ = key
        return default


class ComplexSession(BaseSession, StorageMixin):
    """
    Inherits properties from BaseSession and storage from StorageMixin.
    Implements history/recall itself.
    """
    async def history(self, limit: int = 10, offset: int = 0) -> list[Interaction]:
        _ = (limit, offset)
        return []

    async def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> list[str]:
        _ = (query, limit, threshold)
        return []


def test_session_handle_compliance() -> None:
    """Test that MockSession complies with SessionHandle protocol."""
    mock = MockSession()
    assert isinstance(mock, SessionHandle)


def test_session_handle_incomplete() -> None:
    """Test that IncompleteSession does not comply with SessionHandle protocol."""
    incomplete = IncompleteSession()
    assert not isinstance(incomplete, SessionHandle)


def test_session_handle_sync_edge_case() -> None:
    """
    Test SyncSession behavior.
    Runtime checkable protocols verify method presence, not async/sync nature.
    So this is expected to PASS isinstance check even if semantically wrong.
    """
    sync_mock = SyncSession()
    assert isinstance(sync_mock, SessionHandle)


def test_session_handle_missing_property() -> None:
    """Test compliance fails when property is missing."""
    missing = MissingPropertySession()
    assert not isinstance(missing, SessionHandle)


def test_complex_inheritance_compliance() -> None:
    """Test compliance with multiple inheritance."""
    complex_mock = ComplexSession()
    assert isinstance(complex_mock, SessionHandle)
