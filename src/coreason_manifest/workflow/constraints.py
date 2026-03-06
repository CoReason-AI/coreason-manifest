# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Any

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class StateContract(CoreasonBaseModel):
    """
    A strict Cryptographic State Contract (Typed Blackboard) for multi-agent memory sharing.
    """

    schema_definition: dict[str, Any] = Field(
        description="A strict JSON Schema dictionary defining the required shape of the shared memory blackboard."
    )
    strict_validation: bool = Field(
        default=True,
        description="If True, the orchestrator must reject any state mutation that fails the schema definition.",
    )


class DiversityConstraint(CoreasonBaseModel):
    """
    Constraints enforcing cognitive heterogeneity.
    """

    min_adversaries: int = Field(
        description="The minimum number of adversarial or 'Devil's Advocate' roles required to prevent groupthink."
    )
    model_variance_required: bool = Field(
        description="If True, forces the orchestrator to route sub-agents to different foundational models."
    )
    temperature_variance: float | None = Field(
        default=None, description="Required statistical variance in temperature settings across the council."
    )


class BackpressurePolicy(CoreasonBaseModel):
    """
    Declarative backpressure constraints.
    """

    max_queue_depth: int = Field(
        description="The maximum number of unprocessed messages/observations "
        "allowed between connected nodes before yielding."
    )
    token_budget_per_branch: float | None = Field(
        default=None, description="The maximum token cost allowed per execution branch before rate-limiting."
    )
