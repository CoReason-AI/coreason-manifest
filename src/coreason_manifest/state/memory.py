# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.state.events import AnyStateEvent


class EpistemicLedger(CoreasonBaseModel):
    history: list[AnyStateEvent] = Field(description="An append-only, cryptographic ledger of state events.")

    @model_validator(mode="after")
    def sort_history(self) -> Self:
        self.history.sort(key=lambda event: event.timestamp)
        return self


class WorkingMemorySnapshot(CoreasonBaseModel):
    system_prompt: str = Field(description="The active system prompt guiding the agent's behavior.")
    active_context: dict[str, str] = Field(
        description="A dictionary representing the active context variables for the agent."
    )


class FederatedStateSnapshot(CoreasonBaseModel):
    topology_id: str | None = Field(
        default=None, description="The identifier of the federated topology, if applicable."
    )
