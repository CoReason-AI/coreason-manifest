import pytest


@pytest.mark.evals
def test_schema_import():
    import coreason_manifest  # noqa: F401
