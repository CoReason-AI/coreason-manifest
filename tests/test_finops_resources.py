# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import AgentDefinition
from coreason_manifest.spec.v2.resources import (
    Currency,
    ModelProfile,
    PricingUnit,
    RateCard,
    ResourceConstraints,
)


def test_cost_calculation_simulation() -> None:
    """Verify RateCard cost calculation logic."""
    card = RateCard(
        unit=PricingUnit.TOKEN_1M,
        currency=Currency.USD,
        input_cost=10.00,
        output_cost=30.00,
        fixed_cost_per_request=0.01,
    )

    input_tokens = 1_500_000
    output_tokens = 500_000

    # Manual calculation
    input_units = input_tokens / 1_000_000
    output_units = output_tokens / 1_000_000

    expected_cost = (input_units * card.input_cost) + (output_units * card.output_cost) + card.fixed_cost_per_request

    # 1.5 * 10 + 0.5 * 30 + 0.01 = 15 + 15 + 0.01 = 30.01
    assert expected_cost == 30.01


def test_serialization() -> None:
    """Verify ModelProfile embedding in AgentDefinition and serialization."""
    profile = ModelProfile(
        provider="openai",
        model_id="gpt-4",
        pricing=RateCard(
            input_cost=10.0,
            output_cost=30.0,
        ),
        constraints=ResourceConstraints(context_window_size=128000),
    )

    agent = AgentDefinition(id="agent-1", name="FinOps Agent", role="Accountant", goal="Save money", resources=profile)

    data = agent.model_dump(mode='json', by_alias=True, exclude_none=True)

    assert data["resources"]["provider"] == "openai"
    assert data["resources"]["pricing"]["input_cost"] == 10.0
    assert data["resources"]["constraints"]["context_window_size"] == 128000


def test_validation_constraints() -> None:
    """Verify ResourceConstraints raises ValidationError for negative values."""
    with pytest.raises(ValidationError):
        ResourceConstraints(context_window_size=-100)

    with pytest.raises(ValidationError):
        ResourceConstraints(context_window_size=1000, max_output_tokens=-1)

    with pytest.raises(ValidationError):
        ResourceConstraints(context_window_size=1000, rate_limit_rpm=-5)


def test_immutability() -> None:
    """Verify that models are frozen."""
    card = RateCard(
        input_cost=10.0,
        output_cost=30.0,
    )
    with pytest.raises(ValidationError):
        card.input_cost = 20.0  # type: ignore
