# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import math

from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    ComputeProvisioningIntent,
    EscrowPolicy,
    MarketContract,
    PredictionMarketState,
    RoutingFrontierPolicy,
    TokenBurnReceipt,
)


@given(
    minimum_collateral=st.integers(min_value=-1000000000, max_value=2000000000),
    slashing_penalty=st.integers(min_value=-1000000000, max_value=2000000000),
)
def test_market_contract(minimum_collateral: int, slashing_penalty: int) -> None:
    import pytest
    from pydantic import ValidationError

    expected_mc = max(0, min(minimum_collateral, 1000000000))
    if slashing_penalty > expected_mc:
        with pytest.raises(ValidationError):
            MarketContract(minimum_collateral=minimum_collateral, slashing_penalty=slashing_penalty)
        return
    mc = MarketContract(minimum_collateral=minimum_collateral, slashing_penalty=slashing_penalty)
    assert 0 <= mc.minimum_collateral <= 1000000000
    assert 0 <= mc.slashing_penalty <= mc.minimum_collateral


@given(probs=st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=10))
def test_prediction_market_state(probs: list[float]) -> None:
    probs_dict = {f"h{i}": str(p) for i, p in enumerate(probs)}
    pms = PredictionMarketState(
        market_cid="m1",
        resolution_oracle_condition_cid="c1",
        lmsr_b_parameter="1.5",
        order_book=[],
        current_market_probabilities=probs_dict,
    )
    s = sum(float(v) for v in pms.current_market_probabilities.values())
    assert math.isclose(s, 1.0, abs_tol=1e-5), f"Probabilities do not sum to 1.0: {s}"
    for v in pms.current_market_probabilities.values():
        assert 0.0 <= float(v) <= 1.0, f"Probability out of bounds: {v}"


@given(max_budget=st.integers(min_value=-2000000000, max_value=2000000000))
def test_compute_provisioning_intent(max_budget: int) -> None:
    cpi = ComputeProvisioningIntent(max_budget=max_budget, required_capabilities=[], qos_class="interactive")
    assert 0 <= cpi.max_budget <= 1000000000


@given(
    burn=st.integers(min_value=-2000000000, max_value=2000000000),
    inp=st.integers(min_value=-2000000000, max_value=2000000000),
    out=st.integers(min_value=-2000000000, max_value=2000000000),
)
def test_token_burn_receipt(burn: int, inp: int, out: int) -> None:
    tbr = TokenBurnReceipt(
        event_cid="e1",
        timestamp=100.0,
        tool_invocation_cid="t1",
        input_tokens=inp,
        output_tokens=out,
        burn_magnitude=burn,
    )
    assert 0 <= tbr.burn_magnitude <= 1000000000
    assert 0 <= tbr.input_tokens <= 1000000000
    assert 0 <= tbr.output_tokens <= 1000000000


@given(
    lat=st.integers(min_value=-1000000000, max_value=1000000000),
    cost=st.integers(min_value=-2000000000, max_value=2000000000),
    carbon=st.floats(min_value=-20000.0, max_value=20000.0),
)
def test_routing_frontier_policy(lat: int, cost: int, carbon: float) -> None:
    rfp = RoutingFrontierPolicy(
        max_latency_ms=lat,
        max_cost_magnitude_per_token=cost,
        min_capability_score=0.5,
        tradeoff_preference="balanced",
        max_carbon_intensity_gco2eq_kwh=carbon,
    )
    assert 1 <= rfp.max_latency_ms <= 86400000
    assert 1 <= rfp.max_cost_magnitude_per_token <= 1000000000
    if rfp.max_carbon_intensity_gco2eq_kwh is not None:
        assert 0.0 <= rfp.max_carbon_intensity_gco2eq_kwh <= 10000.0


@given(escrow=st.integers(min_value=-2000000000, max_value=2000000000))
def test_escrow_policy(escrow: int) -> None:
    ep = EscrowPolicy(escrow_locked_magnitude=escrow, release_condition_metric="rc1", refund_target_node_cid="n1")
    assert 0 <= ep.escrow_locked_magnitude <= 1000000000


def test_routing_frontier_policy_invalid_types() -> None:
    import pytest
    from pydantic import ValidationError

    # Test that invalid types pass through pre-validation without a crash,
    # and fail Pydantic's core validation safely instead of a 500 error.
    with pytest.raises(ValidationError, match=r"(?i)validation error"):
        RoutingFrontierPolicy(
            max_latency_ms="invalid",  # type: ignore[arg-type]
            max_cost_magnitude_per_token="invalid",  # type: ignore[arg-type]  # noqa: S106
            min_capability_score="invalid",  # type: ignore[arg-type]
            tradeoff_preference="balanced",
            max_carbon_intensity_gco2eq_kwh="invalid",  # type: ignore[arg-type]
        )

    # Test TypeError fallback
    with pytest.raises(ValidationError, match=r"(?i)validation error"):
        RoutingFrontierPolicy(
            max_latency_ms=None,  # type: ignore[arg-type]
            max_cost_magnitude_per_token=None,  # type: ignore[arg-type]
            min_capability_score=None,  # type: ignore[arg-type]
            tradeoff_preference="balanced",
            max_carbon_intensity_gco2eq_kwh=None,
        )
