# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class ProcessRewardContract(CoreasonBaseModel):
    pruning_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="If a ThoughtBranch's prm_score falls below this threshold, "
        "the orchestrator MUST halt its generation.",
    )
    max_backtracks_allowed: int = Field(
        ge=0,
        description="The absolute limit on how many times the agent can start a new branch "
        "before throwing a SystemFaultEvent.",
    )
    evaluator_model_name: str | None = Field(
        default=None,
        description="The specific PRM model used to score the logic (e.g., 'math-prm-v2').",
    )


class EscalationContract(CoreasonBaseModel):
    uncertainty_escalation_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="The exact Epistemic Uncertainty score that triggers the opening of the Latent Scratchpad.",
    )
    max_latent_tokens_budget: int = Field(
        gt=0,
        description="The maximum number of hidden tokens the orchestrator is authorized to buy "
        "for the internal monologue.",
    )
    max_test_time_compute_ms: int = Field(
        gt=0,
        description="The physical time limit allowed for the scratchpad search before forcing a timeout.",
    )
