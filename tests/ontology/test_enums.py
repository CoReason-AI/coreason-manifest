# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from coreason_manifest.spec.ontology import ActionSpaceCategoryProfile


def test_action_space_category_properties() -> None:
    assert ActionSpaceCategoryProfile.ORACLE.is_stateless is True
    assert ActionSpaceCategoryProfile.SUBSTRATE.is_stateless is False
    assert ActionSpaceCategoryProfile.ORACLE.io_direction == "read"
    assert ActionSpaceCategoryProfile.NODE.allows_composite_topology is True
    assert ActionSpaceCategoryProfile.ORACLE.allows_composite_topology is False
