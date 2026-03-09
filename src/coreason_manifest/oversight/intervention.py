# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:
This file maps the bounded human intervention schemas. This is a STRICTLY REGULATORY BOUNDARY.
These schemas define the Zero-Trust information flow constraints of the swarm.
DO NOT inject kinetic execution logic here.
All policies must be declarative, deterministic, and capable of severing memory access instantly.
"""

from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.identity import WetwareAttestationContract
from coreason_manifest.core.primitives import NodeID

type LifecycleTrigger = Literal[
    "on_start",
    "on_node_transition",
    "before_tool_execution",
    "on_failure",
    "on_consensus_reached",
    "on_max_loops_reached",
]


class BoundedInterventionScope(CoreasonBaseModel):
    """
    Constraints bounding human interaction for interventions.
    """

    allowed_fields: list[str] = Field(description="List of specific fields the human is permitted to mutate.")
    json_schema_whitelist: dict[str, str | int | float | bool | None | list[Any] | dict[str, Any]] = Field(
        description="Strict JSON Schema constraints for the human's input."
    )


class InterventionPolicy(CoreasonBaseModel):
    """
    Proactive oversight hook bound to a specific lifecycle event.
    """

    trigger: LifecycleTrigger = Field(
        description="The exact topological lifecycle event that triggers this intervention."
    )
    scope: BoundedInterventionScope | None = Field(
        default=None,
        description="The strictly typed boundaries for what the human/oversight "
        "system is allowed to mutate during this pause.",
    )
    blocking: bool = Field(
        default=True,
        description="If True, the graph execution halts until a verdict is rendered. "
        "If False, it is an async observation.",
    )


class FallbackSLA(CoreasonBaseModel):
    """
    SLA defining bounds on human intervention delays.
    """

    timeout_seconds: int = Field(gt=0, description="The maximum allowed delay for a human intervention.")
    timeout_action: Literal["fail_safe", "proceed_with_defaults", "escalate"] = Field(
        description="The action to take when the timeout expires."
    )
    escalation_target_node_id: NodeID | None = Field(
        default=None, description="The specific NodeID to route the execution to if the escalate action is triggered."
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
    intervention_request_id: UUID = Field(
        description="The cryptographic nonce uniquely identifying the intervention request."
    )
    target_node_id: NodeID = Field(description="The ID of the target node.")
    approved: bool = Field(description="Indicates whether the proposed action was approved.")
    feedback: str | None = Field(description="Optional feedback provided along with the verdict.")
    attestation: WetwareAttestationContract | None = Field(
        default=None, description="The cryptographic proof provided by the human operator, if required."
    )

    @model_validator(mode="after")
    def verify_attestation_nonce(self) -> "InterventionVerdict":
        """
        Mathematically guarantees that if a cryptographic signature is presented,
        it cannot be a replay attack from a different node in the DAG.
        """
        if self.attestation is not None and self.attestation.dag_node_nonce != self.intervention_request_id:
            raise ValueError(
                "Anti-Replay Lock Triggered: Attestation nonce does not match the intervention request ID."
            )
        return self


class OverrideIntent(CoreasonBaseModel):
    """
    Dictatorial oversight override payload.
    """

    type: Literal["override"] = Field(default="override", description="The type of the intervention payload.")
    authorized_node_id: NodeID = Field(description="The NodeID of the human or agent executing the override.")
    target_node_id: NodeID = Field(description="The NodeID being forcefully overridden.")
    override_action: dict[str, str | int | float | bool | None] = Field(
        description="The exact payload forcefully injected into the state."
    )
    justification: str = Field(
        max_length=2000, description="Cryptographic audit justification for bypassing algorithmic consensus."
    )


class ConstitutionalAmendmentProposal(CoreasonBaseModel):
    """
    Proposed amendment generated in response to normative drift detection.
    """

    type: Literal["constitutional_amendment"] = Field(
        default="constitutional_amendment", description="The strict discriminator for this intervention payload."
    )
    drift_event_id: str = Field(
        description="The CID of the NormativeDriftEvent that justified triggering this proposal."
    )
    proposed_patch: dict[str, Any] = Field(
        description="A strict, structurally bounded JSON Patch (RFC 6902) proposed by the AI "
        "to mutate the GovernancePolicy."
    )
    justification: str = Field(
        description="The AI's natural language structural/logical argument for why this patch resolves the contradiction "
        "without violating the root AnchoringPolicy."
    )


# =========================================================================
# AGENT INSTRUCTION: WARNING - POLYMORPHIC ROUTER
# If you create a new class above, you MUST append it to the AnyInterventionPayload union below.
# Failure to do so will result in a fatal Pydantic discriminator crash at runtime,
# creating a 'Dangling Class' that the orchestrator cannot deserialize.
# =========================================================================

type AnyInterventionPayload = Annotated[
    InterventionRequest | InterventionVerdict | OverrideIntent | ConstitutionalAmendmentProposal,
    Field(discriminator="type"),
]
