# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.state.argumentation import ArgumentGraph
from coreason_manifest.state.differentials import RollbackRequest, TemporalCheckpoint
from coreason_manifest.state.events import AnyStateEvent


class EpistemicLedger(CoreasonBaseModel):
    history: list[AnyStateEvent] = Field(description="An append-only, cryptographic ledger of state events.")
    checkpoints: list[TemporalCheckpoint] = Field(
        default_factory=list, description="Hard temporal anchors allowing O(1) state restoration."
    )
    active_rollbacks: list[RollbackRequest] = Field(
        default_factory=list, description="Causal invalidations actively enforced on the execution tree."
    )

    @model_validator(mode="after")
    def sort_history(self) -> Self:
        self.history.sort(key=lambda event: event.timestamp)
        return self


class WorkingMemorySnapshot(CoreasonBaseModel):
    system_prompt: str = Field(description="The active system prompt guiding the agent's behavior.")
    active_context: dict[str, str] = Field(
        description="A dictionary representing the active context variables for the agent."
    )
    argumentation: ArgumentGraph | None = Field(
        default=None,
        description=(
            "The formal graph of non-monotonic claims and defeasible "
            "attacks currently active in the swarm's working memory."
        ),
    )


class FederatedStateSnapshot(CoreasonBaseModel):
    topology_id: str | None = Field(
        default=None, description="The identifier of the federated topology, if applicable."
    )
