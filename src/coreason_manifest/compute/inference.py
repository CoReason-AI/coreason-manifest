# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from pydantic import Field

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
