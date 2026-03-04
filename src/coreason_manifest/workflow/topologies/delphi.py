from typing import Literal

from pydantic import Field, model_validator

from coreason_manifest.workflow.flow import BaseTopology


class AutomatedDelphiTopology(BaseTopology):
    """
    Represents the configuration and current state of a blinded, multi-agent consensus panel.

    This topology manages an Automated Delphi consensus state machine, enabling mathematically
    sound, asynchronous, and cross-network evaluations where evaluator identities and bids
    can be blinded to reach epistemic consensus.
    """

    topology_type: Literal["DELPHI"] = Field(
        default="DELPHI",
        description="The strictly typed literal discriminator for an Automated Delphi topology.",
    )
    evaluator_nodes: tuple[str, ...] = Field(
        description="The IDs of the agents or human nodes participating in the consensus panel.",
    )
    anonymize_bids: bool = Field(
        description="Indicates if the orchestrator must blind the origin of claims during the execution phase.",
    )
    consensus_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematical percentage of agreement required to resolve the node (e.g., 0.80).",
    )
    max_iterations: int = Field(
        description="How many rounds of bidding are permitted before the topology throws a suspense exception.",
    )
    current_iteration: int = Field(
        description="Tracks the active round of bidding.",
    )
    bidding_schema_reference: str = Field(
        description="The specific Pydantic model name that all bids must conform to.",
    )

    @model_validator(mode="after")
    def validate_iterations(self) -> "AutomatedDelphiTopology":
        if self.current_iteration > self.max_iterations:
            raise ValueError("current_iteration cannot exceed max_iterations.")
        return self
