# Copyright (c) 2026 CoReason, Inc.
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

from coreason_manifest.spec.ontology import (
    SpatialCoordinateProfile,
    SpatialKinematicActionIntent,
)


def test_spatial_kinematic_action_intent_symmetry_valid() -> None:
    """Test valid instantiation with matching lengths."""
    intent = SpatialKinematicActionIntent(
        action_type="click",
        temporal_waypoints_ms=[100, 200, 300],
        bezier_control_points=[
            SpatialCoordinateProfile(x=0.1, y=0.1),
            SpatialCoordinateProfile(x=0.2, y=0.2),
            SpatialCoordinateProfile(x=0.3, y=0.3),
        ],
        target_frame_cid="cid123",
    )
    assert intent.temporal_waypoints_ms == [100, 200, 300]


def test_spatial_kinematic_action_intent_symmetry_sorted() -> None:
    """Test temporal waypoints are mathematically sorted."""
    intent = SpatialKinematicActionIntent(
        action_type="click",
        temporal_waypoints_ms=[300, 100, 200],
        bezier_control_points=[
            SpatialCoordinateProfile(x=0.1, y=0.1),
            SpatialCoordinateProfile(x=0.2, y=0.2),
            SpatialCoordinateProfile(x=0.3, y=0.3),
        ],
        target_frame_cid="cid123",
    )
    assert intent.temporal_waypoints_ms == [100, 200, 300]


def test_spatial_kinematic_action_intent_symmetry_invalid() -> None:
    """Test invalid instantiation with mismatched lengths."""
    with pytest.raises(ValidationError, match="Kinematic Tensor Asymmetry"):
        SpatialKinematicActionIntent(
            action_type="click",
            temporal_waypoints_ms=[100, 200],
            bezier_control_points=[
                SpatialCoordinateProfile(x=0.1, y=0.1),
                SpatialCoordinateProfile(x=0.2, y=0.2),
                SpatialCoordinateProfile(x=0.3, y=0.3),
            ],
            target_frame_cid="cid123",
        )


def test_spatial_kinematic_action_intent_symmetry_empty() -> None:
    """Test valid instantiation when arrays are empty."""
    intent = SpatialKinematicActionIntent(
        action_type="click",
        temporal_waypoints_ms=[],
        bezier_control_points=[],
        target_frame_cid="cid123",
    )
    assert intent.temporal_waypoints_ms == []
