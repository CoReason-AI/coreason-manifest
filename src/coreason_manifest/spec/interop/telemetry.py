from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NodeState(StrEnum):
    """
    Standard lifecycle states for a node execution.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class NodeExecution(BaseModel):
    """
    Telemetry record for a single node execution attempt.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    node_id: str
    state: NodeState
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    error: str | None = None
    timestamp: datetime
    duration_ms: float


class ExecutionSnapshot(BaseModel):
    """
    Current runtime state of a flow execution for visualization.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    node_states: dict[str, NodeState] = Field(
        default_factory=dict, description="Map of node IDs to their current state."
    )
    active_path: list[str] = Field(default_factory=list, description="Ordered list of visited node IDs.")
