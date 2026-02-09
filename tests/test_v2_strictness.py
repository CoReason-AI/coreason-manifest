import pytest
from pydantic import ValidationError
from coreason_manifest.spec.v2.definitions import ManifestMetadata, ManifestV2, AgentDefinition, Workflow
from coreason_manifest.spec.common_base import ManifestBaseModel

def test_manifest_metadata_strictness():
    """
    Ensure ManifestMetadata forbids extra fields.
    """
    try:
        ManifestMetadata(
            name="Test",
            extra_field="should fail"
        )
    except ValidationError as e:
        assert "Extra inputs are not permitted" in str(e)
        return

    pytest.fail("ManifestMetadata should forbid extra fields")

def test_verify_id_mismatch():
    """
    Ensure verify() catches dictionary key vs object ID mismatch.
    """
    agent = AgentDefinition(
        id="agent1",
        name="Agent 1",
        role="Role",
        goal="Goal"
    )

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s", steps={"s": {"type": "placeholder", "id": "s"}}),
        definitions={
            "wrong_key": agent
        }
    )

    errors = manifest.verify()
    if not any("Definition Key Mismatch" in e for e in errors):
        pytest.fail("verify() should detect ID mismatch")

def test_manifest_base_model_docstring():
    """
    Ensure ManifestBaseModel docstring is updated.
    """
    doc = ManifestBaseModel.__doc__
    if "dump" in doc or "to_json" in doc:
        pytest.fail("ManifestBaseModel docstring contains obsolete 'dump' or 'to_json'")

def test_generic_definition_gone():
    """
    Ensure GenericDefinition is completely removed.
    """
    with pytest.raises(ImportError):
        from coreason_manifest.spec.v2.definitions import GenericDefinition

    with pytest.raises(ImportError):
        from coreason_manifest.spec.v2 import GenericDefinition

def test_all_exports_clean():
    """
    Ensure GenericDefinition is not in __all__.
    """
    from coreason_manifest.spec.v2 import definitions
    import coreason_manifest.spec.v2 as v2_pkg

    assert "GenericDefinition" not in definitions.__all__
    assert "GenericDefinition" not in v2_pkg.__all__
