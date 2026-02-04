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

from ..common import CoReasonBaseModel


class Identity(CoReasonBaseModel):
    """A pure, frozen data structure representing an actor (user, agent, system)."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique identifier for the actor (e.g., UUID, slug).")
    name: str = Field(..., description="Human-readable display name.")
    role: Optional[str] = Field(
        None, description="Contextual role (e.g., 'user', 'assistant', 'system')."
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    @classmethod
    def anonymous(cls) -> "Identity":
        """Factory method for a standardized anonymous identity."""
        return cls(id="anonymous", name="Anonymous User", role="user")
