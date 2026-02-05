# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, List, Protocol, runtime_checkable

from ..common.identity import Identity
from ..common.session import Interaction


@runtime_checkable
class SessionHandle(Protocol):
    """Interface for active memory and session management."""

    @property
    def session_id(self) -> str:
        """The unique identifier for the session."""
        ...

    @property
    def identity(self) -> Identity:
        """The identity associated with the session."""
        ...

    async def history(self, limit: int = 10, offset: int = 0) -> List[Interaction]:
        """Retrieve interaction history."""
        ...

    async def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> List[str]:
        """Recall relevant information from memory."""
        ...

    async def store(self, key: str, value: Any) -> None:
        """Store a value in session state."""
        ...

    async def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from session state."""
        ...
