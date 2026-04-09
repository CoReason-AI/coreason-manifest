# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

# Prosperity Public License 3.0
#
# Copyright (c) 2024 Coreason
#
# This software is distributed under the Prosperity Public License 3.0.
# See the LICENSE file for more information.
import contextlib
import math

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    DynamicLayoutManifest,
    EpistemicAttentionState,
    NodeCIDState,
    ObservabilityLODPolicy,
    SE3TransformProfile,
    TelemetryBackpressureContract,
)


@given(depth=st.integers(min_value=200, max_value=400))
def test_ast_thermodynamic_gas_limits(depth: int) -> None:
    """
    Fuzz DynamicLayoutManifest to trigger AST Complexity Overload.
    """
    layout_tstring = f"f'''{{ {'{{' * depth} 1 {'}}' * depth} }}'''"
    with pytest.raises(ValidationError) as exc_info:
        DynamicLayoutManifest(layout_tstring=layout_tstring[:2000], max_ast_node_budget=5)
    assert "AST Complexity Overload" in str(exc_info.value) or "Invalid syntax" in str(exc_info.value)


@given(foveated_privacy_epsilon=st.floats(min_value=0.0, max_value=100.0))
def test_differential_privacy_interlocks(foveated_privacy_epsilon: float) -> None:
    """
    Fuzz ObservabilityLODPolicy to trigger validation error when applying
    differential privacy to an uncoarsened graph.
    """
    with pytest.raises(ValidationError) as exc_info:
        ObservabilityLODPolicy(
            max_rendered_vertices=100,
            spectral_coarsening_active=False,
            telemetry_backpressure=TelemetryBackpressureContract(
                focal_refresh_rate_hz=60,
                peripheral_refresh_rate_hz=30,
                occluded_refresh_rate_hz=1,
            ),
            foveated_privacy_epsilon=foveated_privacy_epsilon,
        )
    assert "Topological Contradiction" in str(exc_info.value)


@settings(suppress_health_check=[HealthCheck.large_base_example, HealthCheck.too_slow, HealthCheck.data_too_large])
@given(hardware_gaze_signature=st.integers(min_value=8193, max_value=10000).map(lambda x: "a" * x))
def test_biometric_signature_bounding(hardware_gaze_signature: str) -> None:
    """
    Test EpistemicAttentionState to trigger validation error when biometric
    signature string exceeds length limit.
    """
    with pytest.raises(ValidationError) as exc_info:
        EpistemicAttentionState(
            origin=SE3TransformProfile(reference_frame_cid="frame-123", x=0.0, y=0.0, z=0.0),
            direction_unit_vector=(1.0, 0.0, 0.0),
            hardware_gaze_signature=hardware_gaze_signature,
        )
    assert "String should have at most 8192 characters" in str(exc_info.value)


def test_ast_thermodynamic_gas_valid_eval() -> None:
    """
    Test valid parsing and AST limit for DynamicLayoutManifest
    """
    manifest = DynamicLayoutManifest(layout_tstring="f'{1}'", max_ast_node_budget=500)
    assert manifest.max_ast_node_budget == 500


@given(depth=st.integers(min_value=200, max_value=400))
def test_ast_thermodynamic_gas_invalid_syntax(depth: int) -> None:
    """
    Test that invalid syntax passes the AST nodes check (handled by base validation instead)
    but we just want to hit the `except SyntaxError: pass` block for the first block.
    """
    layout_tstring = f"1 + {'+' * depth}"
    with contextlib.suppress(ValidationError):
        DynamicLayoutManifest(layout_tstring=layout_tstring, max_ast_node_budget=500)


def test_differential_privacy_valid() -> None:
    """
    Test valid differential privacy interlocks cover the `return self` path.
    """
    policy = ObservabilityLODPolicy(
        max_rendered_vertices=100,
        spectral_coarsening_active=True,
        telemetry_backpressure=TelemetryBackpressureContract(
            focal_refresh_rate_hz=60,
            peripheral_refresh_rate_hz=30,
            occluded_refresh_rate_hz=1,
        ),
        foveated_privacy_epsilon=0.5,
    )
    assert policy.foveated_privacy_epsilon == 0.5


@given(
    dx=st.floats(min_value=-10.0, max_value=10.0),
    dy=st.floats(min_value=-10.0, max_value=10.0),
    dz=st.floats(min_value=-10.0, max_value=10.0),
)
def test_attention_ray_normalization(dx: float, dy: float, dz: float) -> None:
    d_mag = math.hypot(dx, dy, dz)
    if d_mag == 0.0:
        with pytest.raises(ValidationError) as exc_info:
            EpistemicAttentionState(
                origin=SE3TransformProfile(reference_frame_cid="frame-1", x=0, y=0, z=0),
                direction_unit_vector=(0.0, 0.0, 0.0)
            )
        assert "Attention Ray direction cannot be a zero vector" in str(exc_info.value)
    elif not math.isclose(d_mag, 1.0, abs_tol=1e-3):
        with pytest.raises(ValidationError) as exc_info:
             EpistemicAttentionState(
                origin=SE3TransformProfile(reference_frame_cid="frame-1", x=0, y=0, z=0),
                direction_unit_vector=(dx, dy, dz)
            )
        assert "direction vector must be normalized to 1.0" in str(exc_info.value)
    else:
         state = EpistemicAttentionState(
            origin=SE3TransformProfile(reference_frame_cid="frame-1", x=0, y=0, z=0),
            direction_unit_vector=(dx, dy, dz)
        )
         assert state.direction_unit_vector == (dx, dy, dz)


@given(
    node_id1=st.from_regex(r"^[a-zA-Z0-9.\-_:]+$", fullmatch=True).map(lambda x: f"did:node:{x}"),
    node_id2=st.from_regex(r"^[a-zA-Z0-9.\-_:]+$", fullmatch=True).map(lambda x: f"did:node:{x}"),
)
def test_attention_state_canonical_sort(node_id1: str, node_id2: str) -> None:
    state = EpistemicAttentionState(
        origin=SE3TransformProfile(reference_frame_cid="frame-1", x=0, y=0, z=0),
        direction_unit_vector=(1.0, 0.0, 0.0),
        intersected_node_cids=[node_id2, node_id1]
    )
    assert state.intersected_node_cids == sorted([node_id2, node_id1])


@given(depth=st.integers(min_value=10, max_value=50))
def test_ast_thermodynamic_gas_limits_overload_1(depth: int) -> None:
    """Trigger AST Complexity Overload in the first exec block"""
    layout_tstring = "f'''" + "{1}" * depth + "'''"
    with pytest.raises(ValidationError) as exc_info:
        DynamicLayoutManifest(layout_tstring=layout_tstring, max_ast_node_budget=depth - 1)
    assert "AST Complexity Overload" in str(exc_info.value)


@given(depth=st.integers(min_value=10, max_value=50))
def test_ast_thermodynamic_gas_limits_overload_2(depth: int) -> None:
    """Trigger AST Complexity Overload in the second eval block"""
    layout_tstring = "{1}" * depth
    with pytest.raises(ValidationError) as exc_info:
        DynamicLayoutManifest(layout_tstring=layout_tstring, max_ast_node_budget=depth - 1)
    assert "AST Complexity Overload" in str(exc_info.value)
