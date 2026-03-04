# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Annotated, Any, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID


class BoundedInterventionScope(CoreasonBaseModel):
    """
    Constraints bounding human interaction for interventions.
    """

    allowed_fields: list[str] = Field(description="List of specific fields the human is permitted to mutate.")
    json_schema_whitelist: dict[str, str | int | float | bool | None | list[Any] | dict[str, Any]] = Field(
        description="Strict JSON Schema constraints for the human's input."
    )


class FallbackSLA(CoreasonBaseModel):
    """
    SLA defining bounds on human intervention delays.
    """

    timeout_seconds: int = Field(description="The maximum allowed delay for a human intervention.")
    timeout_action: Literal["fail_safe", "proceed_with_defaults", "escalate"] = Field(
        description="The action to take when the timeout expires."
    )


class InterventionRequest(CoreasonBaseModel):
    """
    Emitted when an agent needs human approval or further intervention.
    """

    type: Literal["request"] = Field(default="request", description="The type of the intervention payload.")
    intervention_scope: BoundedInterventionScope | None = Field(
        default=None, description="The scope constraints bounding the intervention."
    )
    fallback_sla: FallbackSLA | None = Field(default=None, description="The SLA constraints on the intervention delay.")
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
