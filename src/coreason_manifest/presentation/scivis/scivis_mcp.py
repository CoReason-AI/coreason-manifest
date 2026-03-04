from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.presentation.scivis.scivis_provenance import ActorIdentity


class MCPToolName(StrEnum):
    """Names of the Universal Canvas API tools."""

    CANVAS_ADD_ELEMENT = "CANVAS_ADD_ELEMENT"
    CANVAS_UPDATE_ELEMENT = "CANVAS_UPDATE_ELEMENT"
    CANVAS_REMOVE_ELEMENT = "CANVAS_REMOVE_ELEMENT"
    CANVAS_GROUP_ELEMENTS = "CANVAS_GROUP_ELEMENTS"
    CANVAS_ADD_CONNECTION = "CANVAS_ADD_CONNECTION"
    CANVAS_APPLY_STYLE = "CANVAS_APPLY_STYLE"
    CANVAS_IMPORT_ARTIFACT = "CANVAS_IMPORT_ARTIFACT"
    CANVAS_ADD_MATH_NODE = "CANVAS_ADD_MATH_NODE"
    CANVAS_UPDATE_MATH_NODE = "CANVAS_UPDATE_MATH_NODE"


class MCPOperation(CoreasonModel):
    """An atomic design action executed on a headless canvas."""

    operation_id: str = Field(..., description="Unique ID for tracing and logging this specific action.")
    tool_name: MCPToolName
    target_element_id: str | None = Field(
        default=None, description="The ID of the specific canvas object being mutated. Crucial for targeted edits."
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="The kwargs payload for the tool (e.g., x, y, width, fill_color)."
    )
    actor: ActorIdentity | None = Field(
        default=None, description="Cryptographically tags the specific agent/human issuing this canvas command."
    )

    @model_validator(mode="after")
    def enforce_strict_provenance(self) -> "MCPOperation":
        if (
            self.tool_name in {MCPToolName.CANVAS_ADD_MATH_NODE, MCPToolName.CANVAS_UPDATE_MATH_NODE}
            and self.actor is None
        ):
            raise ValueError("Regulatory SciVis operations require a cryptographically verifiable ActorIdentity.")
        return self

    @model_validator(mode="after")
    def validate_target_element_id(self) -> "MCPOperation":
        requires_id = {
            MCPToolName.CANVAS_UPDATE_ELEMENT,
            MCPToolName.CANVAS_REMOVE_ELEMENT,
            MCPToolName.CANVAS_UPDATE_MATH_NODE,
        }
        if self.tool_name in requires_id and self.target_element_id is None:
            raise ValueError(f"target_element_id cannot be None when tool_name is {self.tool_name}")
        return self


class MCPOperationSequence(CoreasonModel):
    """An ordered, transactional sequence of atomic design actions."""

    sequence_id: str
    operations: list[MCPOperation]
    transaction_mode: Literal["atomic_commit", "sequential_best_effort"] = Field(
        default="atomic_commit",
        description="If atomic, the downstream engine must snapshot the canvas and rollback if any operation fails.",
    )
    expected_canvas_state_hash: str | None = Field(
        default=None,
        description="Ensures the sequence is applied to the correct diagram version to prevent races.",
    )
