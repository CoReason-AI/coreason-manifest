# Prosperity-3.0
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from coreason_manifest.core.compute.reasoning import ModelRef
from coreason_manifest.core.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.core.oversight.governance import OperationalPolicy
from coreason_manifest.core.primitives.registry import register_node
from coreason_manifest.core.primitives.types import ProfileID, VariableID
from coreason_manifest.core.security.compliance import RemediationAction

from .base import LockConfig, Node


class StatisticalStoppingRule(StrEnum):
    CMH_CORMACK_GROSSMAN = "cmh_cormack_grossman"
    ELKAN_KNEE = "elkan_knee"


class CALConfig(BaseModel):
    """Conformal Active Learning (CAL) Configuration for High-Volume Swarms."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    active_learning_batch_size: Annotated[
        int, Field(gt=0, description="Number of items to process before reprioritizing the queue.")
    ] = 50
    target_recall_percent: Annotated[
        float, Field(ge=0.0, le=1.0, description="Statistical recall threshold to hit before halting execution.")
    ] = 0.95
    stopping_rule: Annotated[
        StatisticalStoppingRule, Field(description="The mathematical method used to calculate recall estimates.")
    ] = StatisticalStoppingRule.CMH_CORMACK_GROSSMAN


class TournamentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    bracket_style: Literal["single_elimination", "round_robin"] = "single_elimination"
    retain_falsified_data: bool = Field(
        True, description="If True, the loser's methodology is logged as an anti-pattern."
    )


@register_node
class SwarmNode(Node):
    """Dynamic Swarm Spawning. Spins up N ephemeral worker agents to process a dataset/workload in parallel."""

    type: Literal["swarm"] = Field("swarm", description="The type of the node.", examples=["swarm"])

    worker_profile: ProfileID = Field(
        ..., description="Reference to a CognitiveProfile ID.", examples=["researcher_profile"]
    )
    workload_variable: VariableID = Field(
        ..., description="The Blackboard list/dataset to process.", examples=["urls_to_scrape"]
    )

    distribution_strategy: Literal["sharded", "replicated", "island_model"] = Field(
        ...,
        description=("Sharded=split data; Replicated=same data, many attempts; island_model=isolated sub-swarms."),
        examples=["sharded"],
    )
    max_concurrency: Annotated[
        int | Literal["infinite"] | None,
        Field(description="Limit parallel workers. Use 'infinite' for no limit.", examples=[10]),
    ]

    failure_tolerance_percent: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description=(
                "0.0 = All must succeed. 0.2 = Allow 20% failure. "
                "Executed AFTER the Node's 'resilience' strategy. "
                "E.g., if retries exhaust, this tolerance allows the Swarm to still succeed partially."
            ),
            examples=[0.1],
        ),
    ] = 0.0

    reducer_function: Literal[
        "concat", "vote", "summarize", "tournament", "tabular_join", "meta_analysis_matrix"
    ] | None = Field(..., description="How to combine results.", examples=["concat"])

    tournament_config: TournamentConfig | None = None

    cal_config: CALConfig | None = Field(
        None, description="Active learning bounds for high-volume screening. If set, overrides standard exhaustion."
    )

    sub_swarm_count: Annotated[
        int | None, Field(description="Required if using island_model. Number of isolated sub-swarms.")
    ] = None

    isolation_turns: Annotated[
        int | None,
        Field(description="Required if using island_model. Number of generations before islands migrate data."),
    ] = None

    pruning_strategy: Literal["none", "early_stopping", "compute_bound"] = Field(
        "none", description="Strategy for dynamically killing failing worker agents."
    )
    aggregator_model: Annotated[
        ModelRef | None,
        Field(
            description="If set, uses this model to summarize the worker outputs into a single string.",
            examples=["gpt-4"],
        ),
    ] = None
    operational_policy: Annotated[
        OperationalPolicy | None,
        Field(
            None,
            description="Local operational limits. Overrides global Governance limits if set.",
            examples=[{"financial": {"max_cost_usd": 50.0}}],
        ),
    ]
    output_variable: VariableID = Field(
        ..., description="Variable to store the aggregated result.", examples=["final_report"]
    )

    export_interoperability: list[Literal["csv", "revman", "r_metafor"]] | None = Field(
        None, description="Required target formats for the aggregated data matrix. Used for downstream biostatistics."
    )

    lock_config: LockConfig | None = Field(
        None,
        description="Atomic lock configuration for preventing race conditions.",
        examples=[{"write_locks": ["shared_resource"]}],
    )

    @model_validator(mode="after")
    def validate_reducer_requirements(self) -> "SwarmNode":
        if self.reducer_function == "tournament" and self.tournament_config is None:
            raise ValueError("SwarmNode with reducer_function='tournament' requires a 'tournament_config'.")

        if self.distribution_strategy == "island_model" and (
            self.sub_swarm_count is None or self.isolation_turns is None
        ):
            raise ValueError(
                "SwarmNode with distribution_strategy='island_model' requires "
                "both 'sub_swarm_count' and 'isolation_turns'."
            )

        if self.pruning_strategy == "compute_bound" and self.operational_policy is None:
            raise ValueError(
                "SwarmNode with pruning_strategy='compute_bound' requires an 'operational_policy' to bind to."
            )

        if self.reducer_function == "summarize" and not self.aggregator_model:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.VAL_SWARM_REDUCER,
                message="SwarmNode with reducer='summarize' requires an 'aggregator_model'.",
                context={
                    "remediation": RemediationAction(
                        type="update_field",
                        target_node_id=self.id,
                        description="Add a default 'aggregator_model'.",
                        patch_data=[
                            {
                                "op": "add",
                                "path": "/aggregator_model",
                                "value": "gpt-4-turbo",  # Reasonable default
                            }
                        ],
                    ).model_dump()
                },
            )
        return self
