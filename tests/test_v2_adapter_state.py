from typing import Any, Dict, Optional

from coreason_manifest.v2.adapter import v2_to_recipe
from coreason_manifest.v2.spec.contracts import StateDefinition as StateDefinitionV2
from coreason_manifest.v2.spec.definitions import ManifestMetadata, ManifestV2, Workflow


def create_manifest(backend: Optional[str] = None, schema: Optional[Dict[str, Any]] = None) -> ManifestV2:
    if schema is None:
        schema = {}
    return ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="test"),
        workflow=Workflow(start="s1", steps={"s1": {"type": "logic", "id": "s1", "code": "pass"}}),
        state=StateDefinitionV2(schema_=schema, backend=backend),
    )


def test_state_schema_mapping() -> None:
    """Test that schema is correctly mapped from V2 to V1."""
    schema = {"user": {"type": "string"}, "count": {"type": "integer"}}
    manifest = create_manifest(schema=schema)
    recipe = v2_to_recipe(manifest)

    assert recipe.state.schema_ == schema


def test_state_backend_mapping_persistent() -> None:
    """Test that backend='persistent' maps to persistence='persistent'."""
    manifest = create_manifest(backend="persistent")
    recipe = v2_to_recipe(manifest)
    assert recipe.state.persistence == "persistent"


def test_state_backend_mapping_redis() -> None:
    """Test that backend='redis' maps to persistence='persistent'."""
    manifest = create_manifest(backend="redis")
    recipe = v2_to_recipe(manifest)
    assert recipe.state.persistence == "persistent"


def test_state_backend_mapping_memory() -> None:
    """Test that backend='memory' maps to persistence='ephemeral'."""
    manifest = create_manifest(backend="memory")
    recipe = v2_to_recipe(manifest)
    assert recipe.state.persistence == "ephemeral"


def test_state_backend_mapping_ephemeral() -> None:
    """Test that backend='ephemeral' maps to persistence='ephemeral'."""
    manifest = create_manifest(backend="ephemeral")
    recipe = v2_to_recipe(manifest)
    assert recipe.state.persistence == "ephemeral"


def test_state_backend_mapping_none() -> None:
    """Test that backend=None maps to persistence='ephemeral'."""
    manifest = create_manifest(backend=None)
    recipe = v2_to_recipe(manifest)
    assert recipe.state.persistence == "ephemeral"
