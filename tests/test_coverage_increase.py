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

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    _DNS_CACHE,
    ComputationalThermodynamicsProfile,
    DynamicLayoutManifest,
    _resolve_and_check_hostname,
)
from coreason_manifest.utils.algebra import align_semantic_manifolds


@given(st.lists(st.sampled_from(["text", "raster_image", "semantic_graph"]), min_size=1, max_size=3))
def test_align_semantic_manifolds_coverage(target_modalities: list[str]) -> None:
    target_modes = list(set(target_modalities))
    res = align_semantic_manifolds("task123", ["text"], target_modes, "event123")  # type: ignore[arg-type]
    if "semantic_graph" in target_modes:
        assert res is not None
        assert res.schema_governance is not None


@given(st.integers(min_value=10, max_value=20))
def test_simple_ttl_cache_eviction(maxsize: int) -> None:
    _DNS_CACHE.maxsize = maxsize
    for i in range(maxsize + 5):
        _DNS_CACHE.set(f"host_{i}", True)
    assert len(_DNS_CACHE.cache) <= maxsize


@given(st.just("example.com"))
def test_resolve_and_check_hostname_example(host: str) -> None:
    # clear cache for this host if present to ensure the branch is hit
    _DNS_CACHE.cache.pop(host, None)
    _resolve_and_check_hostname(host)
    assert _DNS_CACHE.get(host) is True


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_thermodynamics_profile_nan_inf(val: float) -> None:
    if math.isnan(val) or math.isinf(val):
        with pytest.raises(ValidationError):
            ComputationalThermodynamicsProfile(
                thermodynamics_cid="did:coreason:thermo:1",
                target_topology_cid="did:coreason:topo:1",
                computational_free_energy_budget=100.0,
                max_stochastic_diffusions=10,
                current_diffusions=5,
                remaining_free_energy=val,
                entropy_derivative_delta=0.0,
            )


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_thermodynamics_profile_delta_nan_inf(val: float) -> None:
    if math.isnan(val) or math.isinf(val):
        with pytest.raises(ValidationError):
            ComputationalThermodynamicsProfile(
                thermodynamics_cid="did:coreason:thermo:1",
                target_topology_cid="did:coreason:topo:1",
                computational_free_energy_budget=100.0,
                max_stochastic_diffusions=10,
                current_diffusions=5,
                remaining_free_energy=100.0,
                entropy_derivative_delta=val,
            )


@given(st.integers(min_value=1, max_value=5))
def test_dynamic_layout_manifest_overload(budget: int) -> None:
    with pytest.raises(ValidationError, match="AST Complexity Overload"):
        # generate a complex string that will have more AST nodes than the budget
        DynamicLayoutManifest(layout_tstring="{a}" * 50, max_ast_node_budget=budget)
