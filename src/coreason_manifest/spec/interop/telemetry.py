from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class NodeState(StrEnum):
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
    Includes Veritas integrity fields for cryptographic chaining.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    node_id: str
    state: NodeState
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    error: str | None = None
    timestamp: datetime
    duration_ms: float
    attributes: dict[str, str | int | float | bool] = Field(default_factory=dict)

    # --- VERITAS INTEGRITY RESTORATION ---
    execution_hash: Annotated[str | None, Field(description="SHA-256 hash of inputs+outputs+config.")] = None
    previous_hashes: list[str] = Field(
        default_factory=list, description="Hashes of preceding executions (DAG parents)."
    )
    signature: Annotated[str | None, Field(description="Optional cryptographic signature of the event.")] = None

    _hash_exclude_: ClassVar[set[str]] = {"execution_hash", "signature"}


class ExecutionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    node_states: dict[str, NodeState]
    active_path: list[str]
