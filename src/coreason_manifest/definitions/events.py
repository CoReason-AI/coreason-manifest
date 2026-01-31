# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from enum import Enum
from typing import Any, Dict, Optional

from .base import CoReasonBaseModel


class NodeState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class GraphEvent(CoReasonBaseModel):
    """
    Real-time telemetry for the Living Canvas.
    Sent via Redis/SSE to the Frontend.
    """

    execution_id: str
    node_id: str
    timestamp: float
    state: NodeState
    progress: float  # Value between 0.0 and 1.0
    metadata: Optional[Dict[str, Any]] = None
