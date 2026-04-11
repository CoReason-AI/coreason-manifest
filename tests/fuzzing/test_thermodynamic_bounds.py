# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import ComputationalThermodynamics, ThermodynamicState


@given(
    max_diff=st.integers(min_value=1, max_value=1000),
    current_diff=st.integers(min_value=1001, max_value=10000),
    free_energy=st.floats(min_value=0.1, max_value=100.0, exclude_max=False),
    thermo_cid=st.uuids().map(str),
)
def test_diffusion_overload(max_diff: int, current_diff: int, free_energy: float, thermo_cid: str) -> None:
    if current_diff <= max_diff:
        current_diff = max_diff + 1
    with pytest.raises(ValidationError) as exc_info:
        ComputationalThermodynamics(
            thermodynamics_cid=thermo_cid,
            target_topology_cid="topology-1234",
            max_stochastic_diffusions=max_diff,
            computational_free_energy_budget=100.0,
            current_diffusions=current_diff,
            remaining_free_energy=free_energy,
        )
    assert "current_diffusions strictly exceeds max_stochastic_diffusions" in str(exc_info.value)


@given(
    max_diff=st.integers(min_value=1, max_value=1000),
    current_diff=st.integers(min_value=0, max_value=1000),
    free_energy=st.floats(min_value=0.1, max_value=100.0),
    thermo_cid=st.uuids().map(str),
)
def test_valid_operational_state(max_diff: int, current_diff: int, free_energy: float, thermo_cid: str) -> None:
    if current_diff > max_diff:
        current_diff = max_diff
    thermo = ComputationalThermodynamics(
        thermodynamics_cid=thermo_cid,
        target_topology_cid="topology-1234",
        max_stochastic_diffusions=max_diff,
        computational_free_energy_budget=100.0,
        current_diffusions=current_diff,
        remaining_free_energy=free_energy,
    )
    assert thermo.system_state == ThermodynamicState.ACTIVE_DIFFUSION


@given(
    max_diff=st.integers(min_value=1, max_value=1000),
    current_diff=st.integers(min_value=0, max_value=1000),
    free_energy=st.floats(min_value=0.1, max_value=100.0),
    delta=st.floats(min_value=-0.0009, max_value=0.0009),
    thermo_cid=st.uuids().map(str),
)
def test_thermodynamic_stagnation(
    max_diff: int, current_diff: int, free_energy: float, delta: float, thermo_cid: str
) -> None:
    if current_diff > max_diff:
        current_diff = max_diff
    thermo = ComputationalThermodynamics(
        thermodynamics_cid=thermo_cid,
        target_topology_cid="topology-1234",
        max_stochastic_diffusions=max_diff,
        computational_free_energy_budget=100.0,
        current_diffusions=current_diff,
        remaining_free_energy=free_energy,
        entropy_derivative_delta=delta,
        stagnation_tolerance_epsilon=0.001,
    )
    assert thermo.system_state == ThermodynamicState.ENTROPIC_EXHAUSTION_ORACLE_INTERVENTION


@given(
    max_diff=st.integers(min_value=1, max_value=1000),
    current_diff=st.integers(min_value=0, max_value=1000),
    free_energy=st.floats(min_value=0.1, max_value=100.0),
    delta=st.floats(min_value=0.0011, max_value=10.0),
    thermo_cid=st.uuids().map(str),
)
def test_thermodynamic_active_with_valid_delta(
    max_diff: int, current_diff: int, free_energy: float, delta: float, thermo_cid: str
) -> None:
    if current_diff > max_diff:
        current_diff = max_diff
    thermo = ComputationalThermodynamics(
        thermodynamics_cid=thermo_cid,
        target_topology_cid="topology-1234",
        max_stochastic_diffusions=max_diff,
        computational_free_energy_budget=100.0,
        current_diffusions=current_diff,
        remaining_free_energy=free_energy,
        entropy_derivative_delta=delta,
        stagnation_tolerance_epsilon=0.001,
    )
    assert thermo.system_state == ThermodynamicState.ACTIVE_DIFFUSION
