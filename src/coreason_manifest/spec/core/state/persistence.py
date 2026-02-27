from typing import Annotated, Any, Literal

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel

# =========================================================================
#  STATE DIFF (RFC 6902 JSON Patch)
# =========================================================================

PatchOp = Literal["add", "remove", "replace", "move", "copy", "test"]


class StateDiff(CoreasonModel):
    """
    A single operation in an RFC 6902 JSON Patch document.
    """

    op: Annotated[PatchOp, Field(description="The operation to perform.")]
    path: Annotated[str, Field(description="A JSON Pointer path pointing to the target location.")]
    value: Annotated[Any | None, Field(description="The value to add, replace, or test.")] = None
    from_: Annotated[
        str | None,
        Field(alias="from", description="A JSON Pointer path pointing to the source location (for move and copy)."),
    ] = None


# =========================================================================
#  CHECKPOINTING ("Time Travel")
# =========================================================================


class Checkpoint(CoreasonModel):
    """
    A strictly typed contract for a human-in-the-loop rollback and state hydration point.
    """

    thread_id: Annotated[str, Field(description="The unique identifier for the execution thread.")]
    node_id: Annotated[str, Field(description="The ID of the Node where this checkpoint was taken.")]
    state_diff: Annotated[list[StateDiff], Field(description="The RFC 6902 JSON Patch representing the state delta.")]


# =========================================================================
#  PERSISTENCE CONFIGURATION
# =========================================================================

BackendType = Literal["memory", "redis", "postgres", "s3", "sqlite", "local"]


class PersistenceConfig(CoreasonModel):
    """
    Configuration for state persistence backend.
    """

    backend_type: Annotated[BackendType, Field(description="The type of the backend storage system.")]
    ttl_seconds: Annotated[int | None, Field(ge=0, description="Time-to-live for the persisted state in seconds.")] = (
        None
    )
