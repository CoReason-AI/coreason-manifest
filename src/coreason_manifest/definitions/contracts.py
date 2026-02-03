# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from pydantic import ConfigDict, Field

from coreason_manifest.definitions.agent import VersionStr
from coreason_manifest.definitions.base import CoReasonBaseModel


class ContractMetadata(CoReasonBaseModel):
    """Metadata for the Interface Contract.

    Attributes:
        id: Unique Identifier for the Contract (UUID).
        version: Semantic Version of the Contract.
        name: Name of the Contract.
        author: Author of the Contract.
        created_at: Creation timestamp (ISO 8601).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(..., description="Unique Identifier for the Contract (UUID).")
    version: VersionStr = Field(..., description="Semantic Version of the Contract.")
    name: str = Field(..., min_length=1, description="Name of the Contract.")
    author: str = Field(..., min_length=1, description="Author of the Contract.")
    created_at: datetime = Field(..., description="Creation timestamp (ISO 8601).")


class InterfaceDefinition(CoReasonBaseModel):
    """A reusable schema definition for an Agent Capability interface.

    Attributes:
        metadata: Metadata for this interface contract.
        inputs: JSON Schema for arguments.
        outputs: JSON Schema for return values.
        description: Human-readable docstring for this interface.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    metadata: ContractMetadata
    inputs: Dict[str, Any] = Field(..., description="JSON Schema for arguments.")
    outputs: Dict[str, Any] = Field(..., description="JSON Schema for return values.")
    description: str = Field(..., description="Human-readable docstring for this interface.")
