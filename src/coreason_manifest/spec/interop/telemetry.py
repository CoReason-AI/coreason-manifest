from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    # --- TRACE CONTEXT (SOTA Telemetry) ---
    request_id: str | None = Field(default=None, description="Current execution ID (Span ID).")
    parent_request_id: str | None = Field(default=None, description="Parent execution ID.")
    root_request_id: str | None = Field(default=None, description="Trace ID (Root).")

    traceparent: str | None = Field(
        default=None,
        pattern=r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$",
        description="W3C Trace Context: traceparent header"
    )
    tracestate: str | None = Field(default=None, description="W3C Trace Context: tracestate header")

    # --- VERITAS INTEGRITY RESTORATION ---
    hash_version: Literal["v1"] = Field(default="v1", description="Versioning for the hashing strategy.")
    execution_hash: Annotated[str | None, Field(description="SHA-256 hash of inputs+outputs+config.")] = None
    previous_hashes: list[str] = Field(
        default_factory=list, description="Hashes of preceding executions (DAG parents)."
    )
    signature: Annotated[str | None, Field(description="Optional cryptographic signature of the event.")] = None

    _hash_exclude_: ClassVar[set[str]] = {"execution_hash", "signature"}

    @model_validator(mode="after")
    def validate_trace_integrity(self) -> "NodeExecution":
        """
        Enforces strict lineage integrity.
        """
        if self.parent_request_id and not self.root_request_id:
            raise ValueError("Orphaned trace detected.")
        return self


class ExecutionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    node_states: dict[str, NodeState]
    active_path: list[str]
