from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID


class InterventionRequest(CoreasonBaseModel):
    """
    Emitted when an agent needs human approval or further intervention.
    """

    type: Literal["request"] = Field(default="request", description="The type of the intervention payload.")
    target_node_id: NodeID = Field(description="The ID of the target node.")
    context_summary: str = Field(description="A summary of the context requiring intervention.")
    proposed_action: dict[str, str | int | float | bool | None] = Field(
        description="The action proposed by the agent that requires approval."
    )
    adjudication_deadline: float = Field(description="The deadline for adjudication, represented as a UNIX timestamp.")


class InterventionVerdict(CoreasonBaseModel):
    """
    Emitted by a human or oversight AI to resume the swarm.
    """

    type: Literal["verdict"] = Field(default="verdict", description="The type of the intervention payload.")
    target_node_id: NodeID = Field(description="The ID of the target node.")
    approved: bool = Field(description="Indicates whether the proposed action was approved.")
    feedback: str | None = Field(description="Optional feedback provided along with the verdict.")


type AnyInterventionPayload = Annotated[InterventionRequest | InterventionVerdict, Field(discriminator="type")]
