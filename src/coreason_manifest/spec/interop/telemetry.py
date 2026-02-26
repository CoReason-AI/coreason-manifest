from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, ClassVar, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from coreason_manifest.spec.interop.antibody import AntibodyBase


class NodeState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class NodeExecution(AntibodyBase):
    """
    Telemetry record for a single node execution attempt.
    Includes Veritas integrity fields for cryptographic chaining.
    Inherits AntibodyBase for Zero-Trust validation (NaN/Inf quarantine).
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

    # --- TRACE CONTEXT (Standard Telemetry) ---
    request_id: str | None = Field(default=None, description="Current execution ID (Span ID).")
    parent_request_id: str | None = Field(default=None, description="Parent execution ID.")
    root_request_id: str | None = Field(default=None, description="Trace ID (Root).")

    traceparent: str | None = Field(
        default=None,
        pattern=r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$",
        description="W3C Trace Context: traceparent header",
    )
    tracestate: str | None = Field(default=None, description="W3C Trace Context: tracestate header")

    # --- VERITAS INTEGRITY RESTORATION ---
    hash_version: Literal["v2"] = Field(default="v2", description="Cryptographic hashing protocol version.")
    execution_hash: Annotated[str | None, Field(description="SHA-256 hash of inputs+outputs+config.")] = None

    # Topology: Support both Linear (parent_hash) and DAG (parent_hashes)
    parent_hash: str | None = Field(default=None, description="Hash of the single parent execution (Linear).")
    parent_hashes: list[str] = Field(default_factory=list, description="Hashes of preceding executions (DAG parents).")

    signature: Annotated[str | None, Field(description="Optional cryptographic signature of the event.")] = None

    _hash_exclude_: ClassVar[set[str]] = {"execution_hash", "signature"}

    @model_validator(mode="before")
    @classmethod
    def enforce_envelope_consistency(cls, data: Any) -> Any:
        """
        Single-pass pre-validation to enforce both lineage rooting
        and DAG topology consistency, minimizing dict.copy() overhead.
        """
        if isinstance(data, dict):
            # One copy for all mutations
            data = data.copy()

            # 1. Lineage Auto-Rooting
            req_id = data.get("request_id")
            parent = data.get("parent_request_id")
            root = data.get("root_request_id")

            if not req_id:
                req_id = str(uuid4())
                data["request_id"] = req_id

            if not parent and not root:
                data["root_request_id"] = req_id

            # 2. Topology Consistency
            p_hash = data.get("parent_hash")
            prev_hashes = data.get("parent_hashes")

            if p_hash:
                if prev_hashes is None:
                    data["parent_hashes"] = [p_hash]
                elif isinstance(prev_hashes, list) and p_hash not in prev_hashes:
                    new_prev = prev_hashes.copy()
                    new_prev.append(p_hash)
                    data["parent_hashes"] = new_prev

        return data

    @model_validator(mode="after")
    def validate_trace_integrity(self) -> "NodeExecution":
        """
        Enforces strict lineage integrity.
        """
        if self.parent_request_id and not self.root_request_id:
            raise ValueError("Orphaned trace detected.")  # pragma: no cover
        return self


class HumanSteeringEvent(AntibodyBase):
    """
    Records a state mutation injected by a human (Time Travel/Steering).
    Used to preserve the Merkle execution trace when state is altered mid-flight.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    checkpoint_id: str = Field(..., description="Unique ID for this checkpoint.")
    timestamp: datetime = Field(..., description="When the mutation occurred.")
    mutated_variables: dict[str, Any] = Field(..., description="The variables that were changed.")
    human_identity: str = Field(..., description="ID/Email of the human operator.")


class MemoryMutationEvent(AntibodyBase):
    """
    Telemetry record for memory mutations (ADD, UPDATE, DELETE, EVICT, CONSOLIDATE)
    within the 4-tier memory subsystem. Ensures the Merkle DAG lineage isn't broken
    by implicit state changes.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    request_id: str | None = Field(default_factory=lambda: str(uuid4()), description="Unique ID for this mutation event.")
    parent_request_id: str = Field(..., description="The execution ID that triggered this mutation.")
    root_request_id: str = Field(..., description="The trace ID.")
    tier: Literal["working", "episodic", "semantic", "procedural"] = Field(..., description="The memory tier affected.")
    operation: Literal["ADD", "UPDATE", "DELETE", "EVICT", "CONSOLIDATE"] = Field(..., description="The type of mutation.")
    mutation_payload: dict[str, Any] = Field(..., description="The state diff or payload of the mutation.")
    timestamp: datetime = Field(..., description="When the mutation occurred.")


class ExecutionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    node_states: dict[str, NodeState]
    active_path: list[str]
