# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for SE3TransformProfile, VolumetricBoundingProfile, ViewportProjectionContract, EpistemicAttentionState."""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    EpistemicAttentionState,
    SE3TransformProfile,
    SpatialRenderMaterialState,
    ViewportProjectionContract,
    VolumetricBoundingProfile,
)
from tests.ontology.strategies import (
    se3_full_kwargs_strategy,
    unit_vector_strategy,
)

# ---------------------------------------------------------------------------
# SE3TransformProfile
# ---------------------------------------------------------------------------


class TestSE3TransformProfile:
    """Exercise quaternion normalization validator."""

    def test_valid_identity_quaternion(self) -> None:
        obj = SE3TransformProfile(reference_frame_cid="frame-1", x=0.0, y=0.0, z=0.0)
        assert math.isclose(math.hypot(obj.qx, obj.qy, obj.qz, obj.qw), 1.0, abs_tol=1e-3)

    def test_zero_quaternion_rejected(self) -> None:
        with pytest.raises(ValidationError, match="zero vector"):
            SE3TransformProfile(reference_frame_cid="frame-2", x=0.0, y=0.0, z=0.0, qx=0.0, qy=0.0, qz=0.0, qw=0.0)

    def test_unnormalized_quaternion_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"normalized to 1\.0"):
            SE3TransformProfile(reference_frame_cid="frame-3", x=0.0, y=0.0, z=0.0, qx=0.3, qy=0.3, qz=0.3, qw=0.3)

    @given(kwargs=se3_full_kwargs_strategy())
    @settings(max_examples=20, deadline=None)
    def test_normalized_quaternion_always_valid(self, kwargs: dict) -> None:  # type: ignore[type-arg]
        obj = SE3TransformProfile(**kwargs)
        mag = math.hypot(obj.qx, obj.qy, obj.qz, obj.qw)
        assert math.isclose(mag, 1.0, abs_tol=1e-2)


# ---------------------------------------------------------------------------
# VolumetricBoundingProfile
# ---------------------------------------------------------------------------


class TestVolumetricBoundingProfile:
    """Exercise validate_volume_physics validator."""

    def _se3(self) -> SE3TransformProfile:
        return SE3TransformProfile(reference_frame_cid="f1", x=0.0, y=0.0, z=0.0)

    def test_valid_volume(self) -> None:
        obj = VolumetricBoundingProfile(center_transform=self._se3(), extents_x=1.0, extents_y=1.0, extents_z=1.0)
        assert obj.extents_x * obj.extents_y * obj.extents_z > 0.0

    def test_zero_extent_rejected(self) -> None:
        with pytest.raises(ValidationError, match="3D magnitude"):
            VolumetricBoundingProfile(center_transform=self._se3(), extents_x=0.0, extents_y=1.0, extents_z=1.0)

    def test_all_zero_extents_rejected(self) -> None:
        with pytest.raises(ValidationError, match="3D magnitude"):
            VolumetricBoundingProfile(center_transform=self._se3(), extents_x=0.0, extents_y=0.0, extents_z=0.0)

    @given(
        ex=st.floats(min_value=0.01, max_value=100.0),
        ey=st.floats(min_value=0.01, max_value=100.0),
        ez=st.floats(min_value=0.01, max_value=100.0),
    )
    @settings(max_examples=15, deadline=None)
    def test_positive_extents_always_valid(self, ex: float, ey: float, ez: float) -> None:
        obj = VolumetricBoundingProfile(center_transform=self._se3(), extents_x=ex, extents_y=ey, extents_z=ez)
        assert obj.extents_x > 0


# ---------------------------------------------------------------------------
# ViewportProjectionContract
# ---------------------------------------------------------------------------


class TestViewportProjectionContract:
    """Exercise frustum geometry and perspective validator."""

    def test_valid_perspective(self) -> None:
        obj = ViewportProjectionContract(
            projection_class="perspective",
            field_of_view_degrees=90.0,
            clipping_plane_near=0.01,
            clipping_plane_far=1000.0,
        )
        assert obj.clipping_plane_near < obj.clipping_plane_far

    def test_perspective_without_fov_rejected(self) -> None:
        with pytest.raises(ValidationError, match="field_of_view_degrees"):
            ViewportProjectionContract(
                projection_class="perspective",
                clipping_plane_near=0.01,
                clipping_plane_far=1000.0,
            )

    def test_near_greater_than_far_rejected(self) -> None:
        with pytest.raises(ValidationError, match="clipping_plane_near must be strictly less"):
            ViewportProjectionContract(
                projection_class="orthographic",
                clipping_plane_near=100.0,
                clipping_plane_far=1.0,
            )

    def test_near_equals_far_rejected(self) -> None:
        with pytest.raises(ValidationError, match="clipping_plane_near must be strictly less"):
            ViewportProjectionContract(
                projection_class="orthographic",
                clipping_plane_near=1.0,
                clipping_plane_far=1.0,
            )

    def test_orthographic_without_fov_valid(self) -> None:
        obj = ViewportProjectionContract(
            projection_class="orthographic",
            clipping_plane_near=0.01,
            clipping_plane_far=100.0,
        )
        assert obj.field_of_view_degrees is None

    @given(
        near=st.floats(min_value=0.001, max_value=0.1),
        far=st.floats(min_value=1.0, max_value=10000.0),
        fov=st.floats(min_value=1.0, max_value=179.0),
    )
    @settings(max_examples=15, deadline=None)
    def test_valid_perspective_range(self, near: float, far: float, fov: float) -> None:
        obj = ViewportProjectionContract(
            projection_class="perspective",
            field_of_view_degrees=fov,
            clipping_plane_near=near,
            clipping_plane_far=far,
        )
        assert obj.clipping_plane_near < obj.clipping_plane_far


# ---------------------------------------------------------------------------
# EpistemicAttentionState
# ---------------------------------------------------------------------------


class TestEpistemicAttentionState:
    """Exercise unit vector normalization and canonical sort validators."""

    def _se3(self) -> SE3TransformProfile:
        return SE3TransformProfile(reference_frame_cid="af1", x=0.0, y=0.0, z=0.0)

    def test_valid_unit_vector(self) -> None:
        obj = EpistemicAttentionState(
            origin=self._se3(),
            direction_unit_vector=(1.0, 0.0, 0.0),
        )
        mag = math.hypot(*obj.direction_unit_vector)
        assert math.isclose(mag, 1.0, abs_tol=1e-3)

    def test_zero_vector_rejected(self) -> None:
        with pytest.raises(ValidationError, match="zero vector"):
            EpistemicAttentionState(
                origin=self._se3(),
                direction_unit_vector=(0.0, 0.0, 0.0),
            )

    def test_unnormalized_vector_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"normalized to 1\.0"):
            EpistemicAttentionState(
                origin=self._se3(),
                direction_unit_vector=(2.0, 2.0, 2.0),
            )

    def test_intersected_node_cids_sorted(self) -> None:
        obj = EpistemicAttentionState(
            origin=self._se3(),
            direction_unit_vector=(0.0, 0.0, 1.0),
            intersected_node_cids=["did:z:c", "did:z:a", "did:z:b"],
        )
        assert obj.intersected_node_cids == sorted(obj.intersected_node_cids)

    @given(uv=unit_vector_strategy())
    @settings(max_examples=15, deadline=None)
    def test_normalized_vector_always_valid(self, uv: tuple[float, float, float]) -> None:
        obj = EpistemicAttentionState(
            origin=self._se3(),
            direction_unit_vector=uv,
        )
        mag = math.hypot(*obj.direction_unit_vector)
        assert math.isclose(mag, 1.0, abs_tol=1e-2)


# ---------------------------------------------------------------------------
# SpatialRenderMaterialState
# ---------------------------------------------------------------------------


class TestSpatialRenderMaterial:
    """Exercise ensure_material_definition validator."""

    def test_material_urn_only(self) -> None:
        obj = SpatialRenderMaterialState(material_urn="urn:coreason:material:glass")
        assert obj.material_urn is not None

    def test_compiled_shader_only(self) -> None:
        obj = SpatialRenderMaterialState(compiled_shader_cid="shader-123")
        assert obj.compiled_shader_cid is not None

    def test_both_set(self) -> None:
        obj = SpatialRenderMaterialState(
            material_urn="urn:coreason:material:metal",
            compiled_shader_cid="shader-456",
        )
        assert obj.material_urn
        assert obj.compiled_shader_cid

    def test_neither_set_rejected(self) -> None:
        with pytest.raises(ValidationError, match="material_urn or a compiled_shader_cid"):
            SpatialRenderMaterialState()
