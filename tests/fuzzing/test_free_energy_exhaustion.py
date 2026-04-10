# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import ComputationalThermodynamics, ThermodynamicState

@given(
    max_diff=st.integers(min_value=1, max_value=1000),
    current_diff=st.integers(min_value=0, max_value=1000),
    free_energy=st.floats(max_value=0.0, allow_nan=False, allow_infinity=False),
    thermo_cid=st.uuids().map(str),
)
def test_depletion_transition_mapping(max_diff: int, current_diff: int, free_energy: float, thermo_cid: str) -> None:
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
    assert thermo.system_state == ThermodynamicState.ENTROPIC_EXHAUSTION_ORACLE_INTERVENTION

@given(
    max_diff=st.integers(min_value=1, max_value=1000),
    current_diff=st.integers(min_value=0, max_value=1000),
    free_energy_active=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
    free_energy_exhausted=st.floats(max_value=0.0, min_value=-100000.0, allow_nan=False, allow_infinity=False),
    thermo_cid_active=st.uuids().map(str),
    thermo_cid_exhausted=st.uuids().map(str),
)
def test_serialization_isomorphism(
    max_diff: int, current_diff: int, free_energy_active: float, free_energy_exhausted: float, thermo_cid_active: str, thermo_cid_exhausted: str
) -> None:
    if current_diff > max_diff:
        current_diff = max_diff
    thermo_active = ComputationalThermodynamics(
        thermodynamics_cid=thermo_cid_active,
        target_topology_cid="topology-1234",
        max_stochastic_diffusions=max_diff,
        computational_free_energy_budget=100.0,
        current_diffusions=current_diff,
        remaining_free_energy=free_energy_active,
    )
    assert thermo_active.system_state == ThermodynamicState.ACTIVE_DIFFUSION
    serialized_active = thermo_active.model_dump_canonical()
    deserialized_active = ComputationalThermodynamics.model_validate_json(serialized_active)
    assert deserialized_active.thermodynamics_cid == thermo_active.thermodynamics_cid
    assert deserialized_active.target_topology_cid == thermo_active.target_topology_cid
    assert deserialized_active.max_stochastic_diffusions == thermo_active.max_stochastic_diffusions
    assert deserialized_active.current_diffusions == thermo_active.current_diffusions
    assert deserialized_active.remaining_free_energy == thermo_active.remaining_free_energy
    assert deserialized_active.system_state == thermo_active.system_state

    thermo_exhausted = ComputationalThermodynamics(
        thermodynamics_cid=thermo_cid_exhausted,
        target_topology_cid="topology-1234",
        max_stochastic_diffusions=max_diff,
        computational_free_energy_budget=100.0,
        current_diffusions=current_diff,
        remaining_free_energy=free_energy_exhausted,
    )
    assert thermo_exhausted.system_state == ThermodynamicState.ENTROPIC_EXHAUSTION_ORACLE_INTERVENTION
    serialized_exhausted = thermo_exhausted.model_dump_canonical()
    deserialized_exhausted = ComputationalThermodynamics.model_validate_json(serialized_exhausted)
    assert deserialized_exhausted.thermodynamics_cid == thermo_exhausted.thermodynamics_cid
    assert deserialized_exhausted.target_topology_cid == thermo_exhausted.target_topology_cid
    assert deserialized_exhausted.max_stochastic_diffusions == thermo_exhausted.max_stochastic_diffusions
    assert deserialized_exhausted.current_diffusions == thermo_exhausted.current_diffusions
    assert deserialized_exhausted.remaining_free_energy == thermo_exhausted.remaining_free_energy
    assert deserialized_exhausted.system_state == thermo_exhausted.system_state
