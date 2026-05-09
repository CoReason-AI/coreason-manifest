from coreason_manifest.spec.ontology import ActionSpaceCategoryProfile


def test_action_space_category_properties() -> None:
    assert ActionSpaceCategoryProfile.ORACLE.is_stateless is True
    assert ActionSpaceCategoryProfile.SUBSTRATE.is_stateless is False
    assert ActionSpaceCategoryProfile.ORACLE.io_direction == "read"
    assert ActionSpaceCategoryProfile.NODE.allows_composite_topology is True
    assert ActionSpaceCategoryProfile.ORACLE.allows_composite_topology is False
