# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file defines the inference tasks including analogical mapping, active inference, and
causal interventions. This is a STRICTLY KINETIC BOUNDARY. These schemas govern non-deterministic execution
and probabilistic boundaries of the agent's reasoning. DO NOT inject persistent state, database schemas, or
business workflow logic here. All models must map exclusively to mathematical hardware, probabilistic
thresholds, and raw GPU tensor execution.
"""

from typing import Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel


class AnalogicalMappingTask(CoreasonBaseModel):
    task_id: str = Field(min_length=1, description="Unique identifier for this lateral thinking task.")
    source_domain: str = Field(
        description="The unrelated abstract concept space (e.g., 'thermodynamics', 'mycelial networks')."
    )
    target_domain: str = Field(description="The actual problem space currently being solved.")
    required_isomorphisms: int = Field(
        ge=1,
        description="The exact number of structural/logical mappings the agent must "
        "successfully bridge between the two domains.",
    )
    divergence_temperature_override: float = Field(
        ge=0.0, description="The specific high-temperature sampling override required to force this creative leap."
    )


class InterventionalCausalTask(CoreasonBaseModel):
    task_id: str = Field(min_length=1, description="Unique identifier for this causal intervention.")
    target_hypothesis_id: str = Field(description="The hypothesis containing the SCM being tested.")
    intervention_variable: str = Field(
        description="The specific node $X$ in the SCM the agent is forcing to a specific state."
    )
    do_operator_state: str = Field(
        description="The exact value or condition forced upon the intervention_variable, "
        "isolating it from its historical causes."
    )
    expected_causal_information_gain: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematical proof of entropy reduction yielded specifically by "
        "breaking the confounding back-doors.",
    )
    execution_cost_budget_cents: int = Field(
        ge=0, description="The maximum economic expenditure authorized to run this specific causal intervention."
    )


class ActiveInferenceContract(CoreasonBaseModel):
    task_id: str = Field(min_length=1, description="Unique identifier for this active inference execution.")
    target_hypothesis_id: str = Field(description="The HypothesisGenerationEvent this task is attempting to falsify.")
    target_condition_id: str = Field(description="The specific FalsificationCondition being tested.")
    selected_tool_name: str = Field(description="The exact tool from the ActionSpace allocated for this experiment.")
    expected_information_gain: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematically estimated reduction in Epistemic Uncertainty "
        "(entropy) this tool call will yield.",
    )
    execution_cost_budget_cents: int = Field(
        ge=0,
        description="The maximum economic expenditure authorized to run this specific scientific test.",
    )


class EpistemicCompressionSLA(CoreasonBaseModel):
    strict_probability_retention: bool = Field(
        default=True,
        description="If True, forces the resulting SemanticNode to populate its uncertainty_profile.",
    )
    max_allowed_entropy_loss: float = Field(
        ge=0.0,
        le=1.0,
        description="The maximum allowed statistical flattening of the source data. Bounded between [0.0, 1.0].",
    )
    required_grounding_density: Literal["sparse", "dense", "exhaustive"] = Field(
        description=(
            "Dictates the required granularity of the MultimodalTokenAnchor "
            "(e.g., must the model map every single entity, or just the global claim?)."
        )
    )


class EpistemicTransmutationTask(CoreasonBaseModel):
    task_id: str = Field(
        min_length=1, description="Unique identifier for this specific multimodal extraction intervention."
    )
    artifact_event_id: str = Field(description="The CID of the MultimodalArtifact being processed.")
    target_modalities: list[
        Literal["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor"]
    ] = Field(min_length=1, description="The specific SOTA modality resolutions required for this extraction pass.")
    compression_sla: EpistemicCompressionSLA = Field(
        description="The strict mathematical boundary defining the maximum allowed informational entropy loss."
    )
    execution_cost_budget_cents: int | None = Field(
        default=None,
        ge=0,
        description="Optional maximum economic expenditure authorized to run this VLM transmutation.",
    )

    @model_validator(mode="after")
    def validate_grounding_density_for_visuals(self) -> Self:
        if ("tabular_grid" in self.target_modalities or "raster_image" in self.target_modalities) and (
            self.compression_sla.required_grounding_density == "sparse"
        ):
            raise ValueError(
                "Epistemic safety violation: Visual or tabular modalities require strict spatial tracking. "
                "'required_grounding_density' cannot be 'sparse'."
            )
        return self
