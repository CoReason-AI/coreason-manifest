from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.common_base import CoreasonModel

# =========================================================================
#  STATE DIFF (RFC 6902 JSON Patch)
# =========================================================================

PatchOp = Literal["add", "remove", "replace", "move", "copy", "test"]


class StateDiff(CoreasonModel):
    """
    A single operation in an RFC 6902 JSON Patch document.
    """

    op: Annotated[PatchOp, Field(description="The operation to perform.", examples=["add"])]
    path: Annotated[
        str, Field(description="A JSON Pointer path pointing to the target location.", examples=["/user/name"])
    ]
    value: Annotated[
        Any | None, Field(default=None, description="The value to add, replace, or test.", examples=["Alice"])
    ]
    from_: Annotated[
        str | None,
        Field(
            default=None,
            alias="from",
            description="A JSON Pointer path pointing to the source location (for move and copy).",
            examples=["/user/old_name"],
        ),
    ]

    @model_validator(mode="after")
    def validate_rfc6902_semantics(self) -> "StateDiff":
        # Rule A: Move/Copy require 'from'
        if self.op in ("move", "copy") and self.from_ is None:
            raise ValueError(f"RFC 6902 Violation: operation '{self.op}' requires a 'from' path.")

        # Rule B: Add/Replace/Test require 'value'
        # We check model_fields_set to allow explicit `value=None` (JSON null) while rejecting omission
        if self.op in ("add", "replace", "test") and "value" not in self.model_fields_set:
            raise ValueError(f"RFC 6902 Violation: operation '{self.op}' requires a 'value' field.")

        return self


# =========================================================================
#  CHECKPOINTING ("Time Travel")
# =========================================================================


class Checkpoint(CoreasonModel):
    """
    A strictly typed contract for a human-in-the-loop rollback and state hydration point.
    """

    thread_id: Annotated[
        str, Field(description="The unique identifier for the execution thread.", examples=["thread_abc123"])
    ]
    node_id: Annotated[
        str, Field(description="The ID of the Node where this checkpoint was taken.", examples=["node_42"])
    ]
    state_diff: Annotated[
        list[StateDiff],
        Field(
            description="The RFC 6902 JSON Patch representing the state delta.",
            examples=[[{"op": "add", "path": "/status", "value": "paused"}]],
        ),
    ]


# =========================================================================
#  PERSISTENCE CONFIGURATION
# =========================================================================

BackendType = Literal["memory", "redis", "postgres", "s3", "sqlite", "local"]


class PersistenceConfig(CoreasonModel):
    """
    Configuration for state persistence backend.
    """

    backend_type: Annotated[
        BackendType, Field(description="The type of the backend storage system.", examples=["redis"])
    ]
    ttl_seconds: Annotated[
        int | None, Field(ge=0, description="Time-to-live for the persisted state in seconds.", examples=[3600])
    ] = None
