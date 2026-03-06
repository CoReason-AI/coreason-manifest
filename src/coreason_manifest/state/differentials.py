# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Any, Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel

type PatchOperation = Literal["add", "remove", "replace", "copy", "move", "test"]


class StatePatch(CoreasonBaseModel):
    op: PatchOperation = Field(description="The strict RFC 6902 JSON Patch operation.")
    path: str = Field(description="The JSON pointer indicating the exact state vector to mutate.")
    value: Any | None = Field(default=None, description="The payload to insert or test, if applicable.")


class StateDiff(CoreasonBaseModel):
    diff_id: str = Field(description="Unique identifier for this state differential.")
    author_node_id: str = Field(
        description="The exact NodeID of the agent or system that authored this state mutation."
    )
    lamport_timestamp: int = Field(
        ge=0,
        description="Strict scalar logical clock used for deterministic LWW (Last-Writer-Wins) conflict resolution.",
    )
    vector_clock: dict[str, int] = Field(
        description="Causal history mapping of all known NodeIDs to their latest logical "
        "mutation count at the time of authoring."
    )
    patches: list[StatePatch] = Field(
        default_factory=list, description="The exact, ordered sequence of operations to apply."
    )


class RollbackRequest(CoreasonBaseModel):
    request_id: str = Field(description="Unique identifier for the causal rollback operation.")
    target_event_id: str = Field(description="The ID of the corrupted event in the EpistemicLedger to revert to.")
    invalidated_node_ids: list[str] = Field(
        default_factory=list,
        description="A list of nodes whose operational histories are causally tainted and must be flushed.",
    )

    @model_validator(mode="after")
    def sort_invalidated_nodes(self) -> Self:
        object.__setattr__(self, "invalidated_node_ids", sorted(self.invalidated_node_ids))
        return self


class TemporalCheckpoint(CoreasonBaseModel):
    checkpoint_id: str = Field(description="Unique identifier for the temporal anchor.")
    ledger_index: int = Field(description="The exact array index in the EpistemicLedger this checkpoint represents.")
    state_hash: str = Field(
        description="The canonical RFC 8785 SHA-256 hash of the entire topology at this exact index."
    )
