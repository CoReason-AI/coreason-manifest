# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from pydantic import ConfigDict, Field

# Consolidate your base imports here. 
# Ensure 'coreason_manifest' or '..' is correct based on your project structure.
from coreason_manifest.common import CoReasonBaseModel
from .message import ChatMessage, MultiModalInput

class LineageMetadata(CoReasonBaseModel):
    """Metadata for tracking request lineage across boundaries."""
    
    model_config = ConfigDict(frozen=True)

    root_request_id: str
    parent_interaction_id: Optional[str] = None


class Interaction(CoReasonBaseModel):
    """
    Represents a single 'User Request -> Assistant Response' cycle.
    Includes lineage tracking and boundary identification.
    """

    model_config = ConfigDict(frozen=True)

    # Fields from the first definition (Identity & Lineage)
    id: str = Field(..., description="Unique identifier for this interaction.")
    lineage: Optional[LineageMetadata] = Field(None, description="Traceability metadata.")

    # Fields from the second definition (Content & Timing)
    input: Union[MultiModalInput, str, Dict[str, Any]] = Field(
        ..., description="The user input (strict, string, or legacy dict)."
    )
    output: Optional[ChatMessage] = Field(None, description="The assistant's response.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The timestamp of the interaction.",
    )
