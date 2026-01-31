# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator


from datetime import datetime
from typing import Any, Dict, Literal

from pydantic import ConfigDict, Field

from .base import CoReasonBaseModel


class Message(CoReasonBaseModel):
    """
    Represents an inter-agent message in the CoReason ecosystem.
    Used for Council Mode communication.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(..., min_length=1, description="Unique message identifier")
    sender: str = Field(..., min_length=1, description="ID of the sending agent")
    receiver: str = Field(..., min_length=1, description="ID of the receiving agent")
    timestamp: datetime = Field(..., description="Timestamp of the message")
    type: str = Field(..., min_length=1, description="Type of the message")
    content: Dict[str, Any] = Field(..., description="Content payload of the message")
