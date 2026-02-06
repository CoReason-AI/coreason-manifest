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
        return []

    async def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> list[str]:
        return ["fact1"]

    async def store(self, key: str, value: Any) -> None:
        pass

    async def get(self, key: str, default: Any = None) -> Any:
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
        return []

    # Missing recall

    async def store(self, key: str, value: Any) -> None:
        pass

    async def get(self, key: str, default: Any = None) -> Any:
        return default


def test_session_handle_compliance() -> None:
    """Test that MockSession complies with SessionHandle protocol."""
    mock = MockSession()
    assert isinstance(mock, SessionHandle)


def test_session_handle_incomplete() -> None:
    """Test that IncompleteSession does not comply with SessionHandle protocol."""
    incomplete = IncompleteSession()
    assert not isinstance(incomplete, SessionHandle)
