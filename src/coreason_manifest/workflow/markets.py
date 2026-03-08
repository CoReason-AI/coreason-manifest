# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file defines the orchestration market schemas. This is a STRICTLY TOPOLOGICAL BOUNDARY.

These schemas dictate the multi-agent graph geometry and decentralized routing mechanics. DO NOT inject procedural
execution code or synchronous blocking loops. Think purely in terms of graph theory, Byzantine fault tolerance, and
multi-agent market dynamics."""

from typing import Annotated

from pydantic import Field, StringConstraints

from coreason_manifest.core.base import CoreasonBaseModel


class HypothesisStake(CoreasonBaseModel):
    """
    The mathematical record of an agent taking a financial/compute position on a specific causal hypothesis.
    """

    agent_id: Annotated[str, StringConstraints(min_length=1)] = Field(
        description="The ID of the agent placing the stake."
    )
    target_hypothesis_id: Annotated[str, StringConstraints(min_length=1)] = Field(
        description="The exact HypothesisGenerationEvent the agent is betting on."
    )
    staked_cents: int = Field(gt=0, description="The volume of capital or compute budget committed to this position.")
    implied_probability: float = Field(ge=0.0, le=1.0, description="The agent's calculated internal confidence score.")


class PredictionMarketState(CoreasonBaseModel):
    """
    The state of the Automated Market Maker (AMM) using Robin Hanson's

    Logarithmic Market Scoring Rule (LMSR) to ensure infinite liquidity.
    """

    market_id: Annotated[str, StringConstraints(min_length=1)] = Field(description="The ID of the prediction market.")
    resolution_oracle_condition_id: str = Field(
        description="The specific FalsificationCondition ID whose execution will trigger the market payout."
    )
    lmsr_b_parameter: float = Field(
        gt=0.0, description="The liquidity parameter defining the market depth and max loss for the AMM."
    )
    order_book: list[HypothesisStake] = Field(description="The immutable ledger of all stakes placed by the swarm.")
    current_market_probabilities: dict[str, float] = Field(
        description="Mapping of hypothesis IDs to their current LMSR-calculated market price (probability)."
    )


class MarketResolution(CoreasonBaseModel):
    """
    The resolution state of an algorithmic prediction market.
    """

    market_id: Annotated[str, StringConstraints(min_length=1)] = Field(description="The ID of the prediction market.")
    winning_hypothesis_id: str = Field(description="The hypothesis ID that was verified.")
    falsified_hypothesis_ids: list[str] = Field(description="The hypothesis IDs that were falsified.")
    payout_distribution: dict[str, int] = Field(
        description="The deterministic mapping of agent IDs to their earned compute budget/cents "
        "based on Brier scoring."
    )
