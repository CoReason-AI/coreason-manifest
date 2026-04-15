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
    SpatialBillboardContract,
    SpatialRenderMaterial,
    VolumetricEdgeProfile,
)


def test_spatial_render_material_requires_at_least_one_field() -> None:
    """Prove SpatialRenderMaterial rejects construction with neither material_urn nor compiled_shader_cid."""
    with pytest.raises(ValidationError, match="material_urn or a compiled_shader_cid"):
        SpatialRenderMaterial()


def test_spatial_render_material_accepts_urn() -> None:
    """Prove SpatialRenderMaterial accepts a valid material URN."""
    mat = SpatialRenderMaterial(material_urn="urn:coreason:material:glass_refractive")
    assert mat.material_urn == "urn:coreason:material:glass_refractive"


def test_spatial_render_material_accepts_shader_cid() -> None:
    """Prove SpatialRenderMaterial accepts a valid compiled shader CID."""
    mat = SpatialRenderMaterial(compiled_shader_cid="shader-abc-123")
    assert mat.compiled_shader_cid == "shader-abc-123"


@given(
    tension=st.floats(min_value=0.0, max_value=1.0),
    flow_velocity=st.floats(min_value=0.0, max_value=100.0),
    edge_thickness=st.floats(min_value=0.01, max_value=10.0),
    spatial_repulsion_scalar=st.floats(min_value=0.01, max_value=100.0),
)
def test_riemannian_geodesic_repulsion(
    tension: float, flow_velocity: float, edge_thickness: float, spatial_repulsion_scalar: float
) -> None:
    with pytest.raises(ValidationError):
        VolumetricEdgeProfile(
            curve_class="riemannian_geodesic",
            tension=tension,
            flow_velocity=flow_velocity,
            edge_thickness=edge_thickness,
            spatial_repulsion_scalar=0.0,
        )

    # Valid case
    VolumetricEdgeProfile(
        curve_class="riemannian_geodesic",
        tension=tension,
        flow_velocity=flow_velocity,
        edge_thickness=edge_thickness,
        spatial_repulsion_scalar=spatial_repulsion_scalar,
    )


@given(
    anchoring_node_cid=st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True).filter(
        lambda x: len(x) >= 7
    ),
    always_face_camera=st.booleans(),
    occlude_behind_meshes=st.booleans(),
    distance_scaling_factor=st.floats(min_value=0.01, max_value=10.0),
)
def test_billboard_shearing_lock(
    anchoring_node_cid: str,
    always_face_camera: bool,
    occlude_behind_meshes: bool,
    distance_scaling_factor: float,
) -> None:
    with pytest.raises(ValidationError):
        SpatialBillboardContract(
            anchoring_node_cid=anchoring_node_cid,
            always_face_camera=always_face_camera,
            occlude_behind_meshes=occlude_behind_meshes,
            distance_scaling_factor=distance_scaling_factor,
            spherical_cylindrical_lock="none",
        )

    # Valid case
    SpatialBillboardContract(
        anchoring_node_cid=anchoring_node_cid,
        always_face_camera=always_face_camera,
        occlude_behind_meshes=occlude_behind_meshes,
        distance_scaling_factor=0.0,
        spherical_cylindrical_lock="none",
    )
