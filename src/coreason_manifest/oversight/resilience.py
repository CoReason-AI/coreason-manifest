# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID


class QuarantineOrder(CoreasonBaseModel):
    """
    Indicates that a target node should be quarantined.
    """

    type: Literal["quarantine"] = Field(default="quarantine", description="The type of the resilience payload.")
    target_node_id: NodeID = Field(description="The ID of the node to be quarantined.")
    reason: str = Field(description="The reason for the quarantine order.")


class CircuitBreakerTrip(CoreasonBaseModel):
    """
    Indicates that a circuit breaker has been tripped for a target node.
    """

    type: Literal["circuit_breaker"] = Field(
        default="circuit_breaker", description="The type of the resilience payload."
    )
    target_node_id: NodeID = Field(description="The ID of the node for which the circuit breaker was tripped.")
    error_signature: str = Field(description="Signature or summary of the error causing the trip.")


class FallbackTrigger(CoreasonBaseModel):
    """
    Indicates that fallback procedures should be triggered for a target node.
    """

    type: Literal["fallback"] = Field(default="fallback", description="The type of the resilience payload.")
    target_node_id: NodeID = Field(description="The ID of the failing node.")
    fallback_node_id: NodeID = Field(description="The ID of the node to use as a fallback.")


type AnyResiliencePayload = Annotated[
    QuarantineOrder | CircuitBreakerTrip | FallbackTrigger, Field(discriminator="type")
]
