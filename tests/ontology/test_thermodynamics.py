# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for ComputationalThermodynamicsProfileProfile and ActiveInferenceEpochStateState."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ActiveInferenceEpochStateState,
    ComputationalThermodynamicsProfileProfile,
    ThermodynamicState,
)

CID_ST = st.from_regex(r"[a-zA-Z0-9_.:-]{1,30}", fullmatch=True)


# ---------------------------------------------------------------------------
# ComputationalThermodynamicsProfileProfile
# ---------------------------------------------------------------------------


class TestComputationalThermodynamicsProfileProfile:
    """Exercise thermodynamic circuit breakers and NaN/Inf traps."""

    def _make(self, **overrides) -> ComputationalThermodynamicsProfileProfile:  # type: ignore[no-untyped-def]
        defaults = {
            "thermodynamics_cid": "th-1",
            "target_topology_cid": "topo-1",
            "max_stochastic_diffusions": 10,
            "computational_free_energy_budget": 100.0,
            "current_diffusions": 0,
            "remaining_free_energy": 50.0,
        }
        defaults.update(overrides)
        return ComputationalThermodynamicsProfileProfile(**defaults)  # type: ignore[arg-type]

    def test_valid_construction(self) -> None:
        obj = self._make()
        assert obj.system_state == ThermodynamicState.ACTIVE_DIFFUSION

    def test_exceeds_max_diffusions(self) -> None:
        with pytest.raises(ValidationError, match="exceeds max_stochastic_diffusions"):
            self._make(current_diffusions=11)

    def test_nan_remaining_energy_rejected(self) -> None:
        with pytest.raises(ValidationError, match="NaN or Infinity"):
            self._make(remaining_free_energy=float("nan"))

    def test_inf_remaining_energy_rejected(self) -> None:
        with pytest.raises(ValidationError, match="NaN or Infinity"):
            self._make(remaining_free_energy=float("inf"))

    def test_nan_entropy_delta_rejected(self) -> None:
        with pytest.raises(ValidationError, match="NaN or Infinity"):
            self._make(entropy_derivative_delta=float("nan"))

    def test_inf_entropy_delta_rejected(self) -> None:
        with pytest.raises(ValidationError, match="NaN or Infinity"):
            self._make(entropy_derivative_delta=float("inf"))

    def test_circuit_breaker_energy_depletion(self) -> None:
        """remaining_free_energy <= 0.0 triggers state change."""
        obj = self._make(remaining_free_energy=0.0)
        assert obj.system_state == ThermodynamicState.ENTROPIC_EXHAUSTION_ORACLE_INTERVENTION

    def test_circuit_breaker_negative_energy(self) -> None:
        obj = self._make(remaining_free_energy=-1.0)
        assert obj.system_state == ThermodynamicState.ENTROPIC_EXHAUSTION_ORACLE_INTERVENTION

    def test_circuit_breaker_stagnation(self) -> None:
        """Small entropy derivative triggers stagnation circuit breaker."""
        obj = self._make(
            remaining_free_energy=10.0,
            entropy_derivative_delta=0.0001,
            stagnation_tolerance_epsilon=0.001,
        )
        assert obj.system_state == ThermodynamicState.ENTROPIC_EXHAUSTION_ORACLE_INTERVENTION

    def test_no_stagnation_above_epsilon(self) -> None:
        """Entropy derivative above epsilon does NOT trigger stagnation."""
        obj = self._make(
            remaining_free_energy=10.0,
            entropy_derivative_delta=0.1,
            stagnation_tolerance_epsilon=0.001,
        )
        assert obj.system_state == ThermodynamicState.ACTIVE_DIFFUSION

    @given(
        diffusions=st.integers(min_value=0, max_value=9),
        energy=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=20, deadline=None)
    def test_valid_range_stays_active(self, diffusions: int, energy: float) -> None:
        obj = self._make(
            current_diffusions=diffusions,
            remaining_free_energy=energy,
        )
        assert obj.system_state == ThermodynamicState.ACTIVE_DIFFUSION


# ---------------------------------------------------------------------------
# ActiveInferenceEpochStateState
# ---------------------------------------------------------------------------


class TestActiveInferenceEpochStateState:
    """Exercise free energy aggregation validator."""

    def test_valid_construction(self) -> None:
        obj = ActiveInferenceEpochStateState(
            epoch_cid="ep-1",
            current_free_energy=5.0,
        )
        assert obj.current_free_energy == 5.0

    def test_nan_free_energy_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Free Energy cannot be"):
            ActiveInferenceEpochStateState(epoch_cid="ep-2", current_free_energy=float("nan"))

    def test_inf_free_energy_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Free Energy cannot be"):
            ActiveInferenceEpochStateState(epoch_cid="ep-3", current_free_energy=float("inf"))

    def test_negative_free_energy_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Negative free energy"):
            ActiveInferenceEpochStateState(epoch_cid="ep-4", current_free_energy=-1.0)

    @given(fe=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False))
    @settings(max_examples=20, deadline=None)
    def test_non_negative_energy_accepted(self, fe: float) -> None:
        obj = ActiveInferenceEpochStateState(epoch_cid="ep-gen", current_free_energy=fe)
        assert obj.current_free_energy >= 0.0
