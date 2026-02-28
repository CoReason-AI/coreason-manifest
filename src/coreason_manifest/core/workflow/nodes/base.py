# Prosperity-3.0
from enum import StrEnum
from typing import Annotated, Any

from pydantic import Field

from coreason_manifest.core.common.presentation import PresentationHints
from coreason_manifest.core.common_base import CoreasonModel
from coreason_manifest.core.oversight.resilience import ResilienceConfig
from coreason_manifest.core.primitives.types import NodeID, VariableID


class ConstraintOperator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    CONTAINS = "contains"


class Constraint(CoreasonModel):
    """Declarative constraint evaluated before node execution."""

    variable: str = Field(..., description="The Blackboard variable path to check.")
    operator: ConstraintOperator
    value: Any = Field(..., description="The threshold or reference value.")
    required: bool = Field(True, description="If True, failure halts execution. If False, emits a warning.")
    error_message: str | None = Field(None, description="Optional custom error message.")


class LockConfig(CoreasonModel):
    """
    Configuration for atomic locks to prevent race conditions during concurrent execution.
    """

    write_locks: list[VariableID] = Field(
        default_factory=list, description="Variables requiring mutually exclusive write access."
    )
    read_locks: list[VariableID] = Field(default_factory=list, description="Variables requiring shared read access.")


class Node(CoreasonModel):
    """Base class for vertices of the execution graph."""

    id: NodeID = Field(..., description="Unique identifier for the node.", examples=["start_node", "agent_1"])
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata for the node.", examples=[{"created_by": "user123"}]
    )
    resilience: Annotated[
        ResilienceConfig | str | None,
        Field(description="Error handling policy or reference ID.", examples=["retry_policy_1"]),
    ] = None
    presentation: Annotated[
        PresentationHints | None,
        Field(description="UI rendering hints.", examples=[{"x": 100, "y": 200}]),
    ] = None
    type: str = Field(..., description="The type of the node.")
    constraints: list[Constraint] = Field(
        default_factory=list, description="Pre-flight checks evaluated before node execution."
    )
