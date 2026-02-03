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
    """The canonical way to represent an actor in the Coreason ecosystem.

    This composite object carries both the unique identifier and the
    human-readable display name, reducing the need for downstream lookups.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Uniquely identifies an entity.")
    name: str = Field(..., description="Name of the entity, preferably unique.")
    role: Optional[str] = Field(None, description="The role of the entity (e.g., assistant, user, system, tool).")

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    @classmethod
    def anonymous(cls) -> "Identity":
        """Returns a default anonymous identity."""
        return cls(id="anonymous", name="Anonymous User", role="user")
