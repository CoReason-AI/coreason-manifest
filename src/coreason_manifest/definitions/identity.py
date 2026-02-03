# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Optional

from pydantic import ConfigDict, Field

from coreason_manifest.definitions.base import CoReasonBaseModel


class Identity(CoReasonBaseModel):
    """Canonical representation of an actor in the Coreason ecosystem.

    Identifies entities (users, agents, tools) participating in a session
    with both a unique ID and a human-readable display name.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique identifier for the entity.")
    name: str = Field(..., description="Display name for UI/Logs.")
    role: Optional[str] = Field(None, description="Role of the entity (e.g., 'assistant', 'user', 'system').")

    def __str__(self) -> str:
        """Return the string representation 'name (id)'."""
        return f"{self.name} ({self.id})"

    @classmethod
    def anonymous(cls) -> "Identity":
        """Return a default anonymous identity."""
        return cls(id="anonymous", name="Anonymous User", role="user")
