import pytest

from coreason_manifest.spec.domains.scientific_vis import DataArtifactElement


def test_data_artifact_element_instantiation() -> None:
    # Test valid instantiation
    element = DataArtifactElement(
        id="node-123", semantic_role="distribution_scatter_plot", artifact_uri="file:///tmp/artifacts/scatter_plot.svg"
    )

    assert element.id == "node-123"
    assert element.semantic_role == "distribution_scatter_plot"
    assert element.artifact_uri == "file:///tmp/artifacts/scatter_plot.svg"
    assert element.maintain_aspect_ratio is True

    # Test custom maintain_aspect_ratio
    element_no_aspect = DataArtifactElement(
        id="node-456",
        semantic_role="results_bar_chart",
        artifact_uri="s3://bucket/bar_chart.svg",
        maintain_aspect_ratio=False,
    )
    assert element_no_aspect.maintain_aspect_ratio is False


def test_data_artifact_element_missing_required() -> None:
    # Test missing required fields
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DataArtifactElement(id="node-123", semantic_role="distribution_scatter_plot")
