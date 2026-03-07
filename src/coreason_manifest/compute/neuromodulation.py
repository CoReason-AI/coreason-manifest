# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class ActivationSteeringContract(CoreasonBaseModel):
    """
    Hardware-level contract for Representation Engineering via activation injection/ablation.
    """

    steering_vector_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$",
        description="The SHA-256 hash of the extracted RepE control tensor (e.g., the 'caution' vector).",
    )
    injection_layers: list[int] = Field(
        min_length=1,
        description="The specific transformer layer indices where this vector must be applied.",
    )
    scaling_factor: float = Field(
        description="The mathematical magnitude/strength of the injection (can be negative for ablation).",
    )
    vector_modality: Literal["additive", "ablation", "clamping"] = Field(
        description="The tensor operation to perform: add the vector, subtract it, or clamp activations to its bounds.",
    )


class CognitiveRoutingDirective(CoreasonBaseModel):
    """
    Hardware-level contract overriding MoE routing to enforce functional/specialist paths.
    """

    dynamic_top_k: int = Field(
        ge=1,
        description="The exact number of functional experts the router must activate per token. "
        "High values simulate deep cognitive strain.",
    )
    routing_temperature: float = Field(
        ge=0.0,
        description="The temperature applied to the router's softmax gate, "
        "controlling how deterministically it picks experts.",
    )
    expert_logit_biases: dict[str, float] = Field(
        default_factory=dict,
        description="Explicit tensor biases applied to the router gate. "
        "Keys are expert IDs (e.g., 'expert_falsifier'), values are logit modifiers.",
    )
    enforce_functional_isolation: bool = Field(
        default=False,
        description="If True, the orchestrator applies a hard mask (-inf) "
        "to any expert not explicitly boosted in expert_logit_biases.",
    )
