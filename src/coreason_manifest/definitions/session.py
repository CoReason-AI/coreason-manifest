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

from ..common import CoReasonBaseModel
from .message import ChatMessage, MultiModalInput


class Interaction(CoReasonBaseModel):
    """Represents a single 'User Request -> Assistant Response' cycle."""

    model_config = ConfigDict(frozen=True)

    input: Union[MultiModalInput, str, Dict[str, Any]] = Field(
        ..., description="The user input (strict, string, or legacy dict)."
    )
    output: Optional[ChatMessage] = Field(None, description="The assistant's response.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The timestamp of the interaction.",
    )
