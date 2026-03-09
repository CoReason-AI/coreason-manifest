# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file defines the orchestration auction schemas. This is a STRICTLY TOPOLOGICAL BOUNDARY.
These schemas dictate the multi-agent graph geometry and decentralized routing mechanics. DO NOT inject procedural
execution code or synchronous blocking loops. Think purely in terms of graph theory, Byzantine fault tolerance, and
multi-agent market dynamics."""

from typing import Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel

type AuctionType = Literal["sealed_bid", "dutch", "vickrey"]
type TieBreaker = Literal["lowest_cost", "lowest_latency", "highest_confidence", "random"]


class AuctionPolicy(CoreasonBaseModel):
    auction_type: AuctionType = Field(description="The market mechanism governing the auction.")
    tie_breaker: TieBreaker = Field(description="The deterministic rule for resolving tied bids.")
    max_bidding_window_ms: int = Field(
        description="The absolute timeout in milliseconds for nodes to submit proposals."
    )


class TaskAnnouncement(CoreasonBaseModel):
    task_id: str = Field(description="Unique identifier for the required task.")
    required_action_space_id: str | None = Field(
        default=None, description="Optional restriction forcing bidders to possess a specific toolset."
    )
    max_budget_magnitude: int = Field(description="The absolute ceiling price the orchestrator is willing to pay.")


class EscrowPolicy(CoreasonBaseModel):
    escrow_locked_magnitude: int = Field(
        ge=0, description="The strictly typed integer amount cryptographically locked prior to execution."
    )
    release_condition_metric: str = Field(
        description="A declarative pointer to the SLA or QA rubric required to release the funds."
    )
    refund_target_node_id: str = Field(
        description="The exact NodeID to return funds to if the release condition fails."
    )


class AgentBid(CoreasonBaseModel):
    agent_id: str = Field(description="The NodeID of the bidder.")
    estimated_cost_magnitude: int = Field(description="The node's calculated cost to fulfill the task.")
    estimated_latency_ms: int = Field(ge=0, description="The node's estimated time to completion.")
    estimated_carbon_gco2eq: float = Field(
        ge=0.0,
        description="The agent's mathematical projection of the environmental cost to execute this inference task.",
    )
    confidence_score: float = Field(ge=0.0, le=1.0, description="The node's epistemic certainty of success.")


class TaskAward(CoreasonBaseModel):
    task_id: str = Field(description="The identifier of the resolved task.")
    awarded_syndicate: dict[str, int] = Field(
        description="Strict mapping of agent NodeIDs to their exact fractional payout in magnitude."
    )
    cleared_price_magnitude: int = Field(description="The final cryptographic clearing price.")
    escrow: EscrowPolicy | None = Field(
        default=None, description="The conditional escrow locking the compute budget."
    )

    @model_validator(mode="after")
    def validate_escrow_bounds(self) -> Self:
        """Ensures locked funds do not exceed the cleared auction price."""
        if self.escrow is not None and self.escrow.escrow_locked_magnitude > self.cleared_price_magnitude:
            raise ValueError("Escrow locked amount cannot exceed the total cleared price.")
        return self

    @model_validator(mode="after")
    def verify_syndicate_allocation(self) -> Self:
        if sum(self.awarded_syndicate.values()) != self.cleared_price_magnitude:
            raise ValueError("Syndicate allocation sum must exactly equal cleared_price_magnitude")
        return self


class AuctionState(CoreasonBaseModel):
    announcement: TaskAnnouncement = Field(description="The original call for proposals.")
    bids: list[AgentBid] = Field(default_factory=list, description="The array of received bids.")
    award: TaskAward | None = Field(
        default=None, description="The final cryptographic receipt of the auction, if resolved."
    )

    clearing_timeout: int = Field(gt=0, description="Maximum wait time for auction settlement.")
    """
    MATHEMATICAL BOUNDARY: Must be > 0. Defines the absolute execution ceiling before forced timeout.
    """

    minimum_tick_size: float = Field(gt=0.0, description="The smallest allowable bid increment.")
    """
    MATHEMATICAL BOUNDARY: Must be > 0.0. Negative or zero tick sizes will instantly trigger validation faults.
    """

    @model_validator(mode="after")
    def sort_bids(self) -> Self:
        """Mathematically sort bids by agent_id for deterministic hashing."""
        object.__setattr__(self, "bids", sorted(self.bids, key=lambda bid: bid.agent_id))
        return self
