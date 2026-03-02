import pytest


@pytest.mark.evals
def test_schema_import() -> None:
    """Verify that the coreason_manifest schema can be imported."""
    import coreason_manifest

    assert coreason_manifest is not None
