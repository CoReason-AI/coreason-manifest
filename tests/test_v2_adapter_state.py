import pytest
from coreason_manifest.v2.adapter import v2_to_recipe
from coreason_manifest.v2.spec.definitions import ManifestV2, ManifestMetadata, Workflow
from coreason_manifest.v2.spec.contracts import StateDefinition as StateDefinitionV2

def create_manifest(backend=None, schema=None):
    if schema is None:
        schema = {}
    return ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="test"),
        workflow=Workflow(start="s1", steps={"s1": {"type": "logic", "id": "s1", "code": "pass"}}),
        state=StateDefinitionV2(
            schema=schema,
            backend=backend
        )
    )

def test_state_schema_mapping():
    """Test that schema is correctly mapped from V2 to V1."""
    schema = {"user": {"type": "string"}, "count": {"type": "integer"}}
    manifest = create_manifest(schema=schema)
    recipe = v2_to_recipe(manifest)

    assert recipe.state.schema_ == schema

def test_state_backend_mapping_persistent():
    """Test that backend='persistent' maps to persistence='persistent'."""
    manifest = create_manifest(backend="persistent")
    recipe = v2_to_recipe(manifest)
    assert recipe.state.persistence == "persistent"

def test_state_backend_mapping_redis():
    """Test that backend='redis' maps to persistence='persistent'."""
    manifest = create_manifest(backend="redis")
    recipe = v2_to_recipe(manifest)
    assert recipe.state.persistence == "persistent"

def test_state_backend_mapping_memory():
    """Test that backend='memory' maps to persistence='ephemeral'."""
    manifest = create_manifest(backend="memory")
    recipe = v2_to_recipe(manifest)
    assert recipe.state.persistence == "ephemeral"

def test_state_backend_mapping_ephemeral():
    """Test that backend='ephemeral' maps to persistence='ephemeral'."""
    manifest = create_manifest(backend="ephemeral")
    recipe = v2_to_recipe(manifest)
    assert recipe.state.persistence == "ephemeral"

def test_state_backend_mapping_none():
    """Test that backend=None maps to persistence='ephemeral'."""
    manifest = create_manifest(backend=None)
    recipe = v2_to_recipe(manifest)
    assert recipe.state.persistence == "ephemeral"
