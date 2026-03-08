# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the Cognitive Routing and Latent Smoothing profiles. This is a STRICTLY
KINETIC BOUNDARY. These schemas define the mathematical physics and 'biochemistry' of the agent's forward
pass. DO NOT inject persistent state or database logic here. All bounds must map to continuous probabilistic
thresholds and tensor manipulations.
"""

from typing import Literal, Self

from pydantic import Field, model_validator

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


class LatentSmoothingProfile(CoreasonBaseModel):
    """The mathematical curve used to gently taper an adversarial activation to prevent logit collapse."""

    decay_function: Literal["linear", "exponential", "cosine_annealing"] = Field(
        description="The trigonometric or algebraic function governing the attenuation curve."
    )
    transition_window_tokens: int = Field(
        gt=0,
        description="The exact number of forward-pass generation steps over which the decay is applied.",
    )
    decay_rate_param: float | None = Field(
        default=None,
        description="The optional tuning parameter (e.g., half-life lambda for exponential decay).",
    )


class SaeLatentFirewall(CoreasonBaseModel):
    """A real-time mechanistic interpretability boundary that monitors and controls specific neural circuits."""

    target_feature_index: int = Field(
        ge=0,
        description="The exact dimensional index of the monosemantic feature in the Sparse Autoencoder dictionary.",
    )
    monitored_layers: list[int] = Field(
        min_length=1,
        description="The specific transformer layer indices where this feature activation must be monitored.",
    )
    max_activation_threshold: float = Field(
        ge=0.0,
        description="The mathematical magnitude limit. If the feature activates beyond this, the firewall trips.",
    )
    violation_action: Literal["clamp", "halt", "quarantine", "smooth_decay"] = Field(
        description="The tensor-level remediation applied when the threshold is breached.",
    )
    clamp_value: float | None = Field(
        default=None,
        description="If violation_action is 'clamp', the physical value to which the activation tensor is forced.",
    )
    sae_dictionary_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$",
        description="The SHA-256 hash of the exact SAE projection matrix required to decode this feature.",
    )
    smoothing_profile: LatentSmoothingProfile | None = Field(
        default=None,
        description="The geometric parameters for continuous attenuation if violation_action is 'smooth_decay'.",
    )

    @model_validator(mode="after")
    def validate_smooth_decay(self) -> Self:
        if self.violation_action == "smooth_decay":
            if self.smoothing_profile is None:
                raise ValueError("smoothing_profile must be provided when violation_action is 'smooth_decay'.")
            if self.clamp_value is None:
                raise ValueError(
                    "clamp_value must be provided as the target asymptote when violation_action is 'smooth_decay'."
                )
        return self


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
