# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class BaseStateEvent(CoreasonBaseModel):
    event_id: str = Field(description="A unique identifier for the event.")
    timestamp: float = Field(description="The timestamp when the event occurred.")


class ObservationEvent(BaseStateEvent):
    type: Literal["observation"] = Field(
        default="observation", description="Discriminator type for an observation event."
    )
    # Adding arbitrary payload to make it useful, even though not explicitly asked,
    # to be safe, I'll just stick strictly to the requested structure or minimalist


class BeliefUpdateEvent(BaseStateEvent):
    type: Literal["belief_update"] = Field(
        default="belief_update", description="Discriminator type for a belief update event."
    )


class SystemFaultEvent(BaseStateEvent):
    type: Literal["system_fault"] = Field(
        default="system_fault", description="Discriminator type for a system fault event."
    )


type AnyStateEvent = Annotated[
    ObservationEvent | BeliefUpdateEvent | SystemFaultEvent,
    Field(discriminator="type", description="A discriminated union of state events."),
]
