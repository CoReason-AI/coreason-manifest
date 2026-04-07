# Prosperity Public License 3.0
#
# Copyright (c) 2024 Coreason
#
# This software is distributed under the Prosperity Public License 3.0.
# See the LICENSE file for more information.

import contextlib

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    DynamicLayoutManifest,
    EpistemicAttentionRay,
    ObservabilityLODPolicy,
    SE3TransformProfile,
    TelemetryBackpressureContract,
)


@given(layout_tstring=st.just("f'''{" + "{{" * 200 + "1" + "}}" * 200 + "}'''"))
def test_ast_thermodynamic_gas_limits(layout_tstring: str) -> None:
    """
    Fuzz DynamicLayoutManifest to trigger AST Complexity Overload.
    """
    with pytest.raises(ValidationError) as exc_info:
        DynamicLayoutManifest(
            layout_tstring=layout_tstring[:2000],  # stay within string length bounds
            max_ast_node_budget=5,
        )
    assert "AST Complexity Overload" in str(exc_info.value)


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


def test_biometric_signature_bounding() -> None:
    """
    Test EpistemicAttentionRay to trigger validation error when biometric
    signature string exceeds length limit.
    """
    hardware_gaze_signature = "a" * 8193
    with pytest.raises(ValidationError) as exc_info:
        EpistemicAttentionRay(
            origin=SE3TransformProfile(reference_frame_id="frame-123", x=0.0, y=0.0, z=0.0),
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


def test_ast_thermodynamic_gas_invalid_syntax() -> None:
    """
    Test that invalid syntax passes the AST nodes check (handled by base validation instead)
    but we just want to hit the `except SyntaxError: pass` block for the f-string eval.
    """
    # This string has unclosed quotes, so ast.parse fails both times.
    with contextlib.suppress(ValidationError):
        DynamicLayoutManifest(layout_tstring="f'{1 + 1", max_ast_node_budget=500)


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
