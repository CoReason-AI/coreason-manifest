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

from coreason_manifest.spec.ontology import (
    DynamicManifoldProjectionManifest,
    EpistemicHydrationPolicy,
    GrammarPanelProfile,
    MCPClientIntent,
    SemanticZoomProfile,
    TelemetryBackpressureContract,
)


@given(
    max_unfold_depth=st.integers(max_value=0) | st.integers(min_value=101),
    lazy_fetch_timeout_ms=st.integers(min_value=1, max_value=60000),
    truncation_strategy=st.sampled_from(["hash_pointer", "nullify", "scalar_summary"]),
)
def test_epistemic_hydration_policy_max_depth_bounds(
    max_unfold_depth: int, lazy_fetch_timeout_ms: int, truncation_strategy: str
) -> None:
    """
    Test that initializing EpistemicHydrationPolicy with an invalid max_unfold_depth raises a ValidationError.
    """
    with pytest.raises(ValidationError) as excinfo:
        EpistemicHydrationPolicy(
            max_unfold_depth=max_unfold_depth,
            lazy_fetch_timeout_ms=lazy_fetch_timeout_ms,
            truncation_strategy=truncation_strategy,  # type: ignore[arg-type]
        )

    assert "max_unfold_depth" in str(excinfo.value)


@given(
    max_unfold_depth=st.integers(min_value=1, max_value=100),
    lazy_fetch_timeout_ms=st.integers(max_value=0) | st.integers(min_value=60001),
    truncation_strategy=st.sampled_from(["hash_pointer", "nullify", "scalar_summary"]),
)
def test_epistemic_hydration_policy_timeout_bounds(
    max_unfold_depth: int, lazy_fetch_timeout_ms: int, truncation_strategy: str
) -> None:
    """
    Test that initializing EpistemicHydrationPolicy with an invalid lazy_fetch_timeout_ms raises a ValidationError.
    """
    with pytest.raises(ValidationError) as excinfo:
        EpistemicHydrationPolicy(
            max_unfold_depth=max_unfold_depth,
            lazy_fetch_timeout_ms=lazy_fetch_timeout_ms,
            truncation_strategy=truncation_strategy,  # type: ignore[arg-type]
        )

    assert "lazy_fetch_timeout_ms" in str(excinfo.value)


def test_epsilon_velocity_bounds_validation() -> None:
    # focal_refresh_rate_hz must be > 60 when epsilon_derivative_threshold == 0.0 to raise error
    with pytest.raises(ValidationError) as excinfo:
        TelemetryBackpressureContract(
            focal_refresh_rate_hz=120,
            peripheral_refresh_rate_hz=60,
            occluded_refresh_rate_hz=0,
            epsilon_derivative_threshold=0.0,
        )
    assert "Thermodynamic Violation" in str(excinfo.value)


def test_epsilon_velocity_bounds_pass() -> None:
    # focal_refresh_rate_hz <= 60 when epsilon_derivative_threshold == 0.0 should pass
    contract = TelemetryBackpressureContract(
        focal_refresh_rate_hz=60,
        peripheral_refresh_rate_hz=30,
        occluded_refresh_rate_hz=0,
        epsilon_derivative_threshold=0.0,
    )
    assert contract.focal_refresh_rate_hz == 60


def test_holographic_resolution_validation() -> None:
    with pytest.raises(ValidationError) as excinfo:
        MCPClientIntent(jsonrpc="2.0", id="req-123", method="mcp.ui.emit_intent", holographic_projection=None)
    assert "Holographic Projection Violation" in str(excinfo.value)


def test_holographic_resolution_pass() -> None:
    # Valid intent if not "mcp.ui.emit_intent"
    # Actually the only valid method for MCPClientIntent is "mcp.ui.emit_intent"
    # So we construct a full holographic_projection dummy to pass validation
    intent = MCPClientIntent(
        jsonrpc="2.0",
        id="req-123",
        method="mcp.ui.emit_intent",
        holographic_projection=DynamicManifoldProjectionManifest(
            manifest_cid="mani-123",
            active_forge_cid="node-1",
            ast_gradient_visual_mapping=GrammarPanelProfile(
                panel_cid="panel-124",
                title="Title",
                ledger_source_cid="node-123",
                mark="point",
                encodings=[],
            ),
            thermodynamic_burn_mapping=GrammarPanelProfile(
                panel_cid="panel-123",
                title="Title",
                ledger_source_cid="node-123",
                mark="point",
                encodings=[],
            ),
            viewport_zoom_profile=SemanticZoomProfile(
                macro_distance_threshold=100.0,
                meso_distance_threshold=50.0,
                micro_distance_threshold=10.0,
            ),
        ),
    )
    assert intent.holographic_projection is not None
