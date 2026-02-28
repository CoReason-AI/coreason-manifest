# Prosperity-3.0
from typing import Annotated, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.compliance import RemediationAction
from coreason_manifest.core.compute.reasoning import ModelRef
from coreason_manifest.core.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.core.oversight.governance import OperationalPolicy
from coreason_manifest.core.primitives.registry import register_node
from coreason_manifest.core.primitives.types import ProfileID, VariableID

from .base import LockConfig, Node


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

    distribution_strategy: Literal["sharded", "replicated"] = Field(
        ..., description="Sharded=split data; Replicated=same data, many attempts.", examples=["sharded"]
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

    reducer_function: Literal["concat", "vote", "summarize"] | None = Field(
        ..., description="How to combine results.", examples=["concat"]
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

    lock_config: LockConfig | None = Field(
        None,
        description="Atomic lock configuration for preventing race conditions.",
        examples=[{"write_locks": ["shared_resource"]}],
    )

    @model_validator(mode="after")
    def validate_reducer_requirements(self) -> "SwarmNode":
        if self.reducer_function == "summarize" and not self.aggregator_model:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_SWARM_REDUCER,
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
