import pytest
from pydantic import ValidationError

from coreason_manifest.spec.common_base import ManifestBaseModel
from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestMetadata, ManifestV2, Workflow
from coreason_manifest.spec.v2.packs import MCPResourceDefinition


def test_manifest_metadata_strictness() -> None:
    """
    Ensure ManifestMetadata forbids extra fields.
    """
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ManifestMetadata.model_validate({"name": "Test", "extra_field": "should fail"})


def test_verify_id_mismatch() -> None:
    """
    Ensure verify() catches dictionary key vs object ID mismatch.
    """
    agent = AgentDefinition(id="agent1", name="Agent 1", role="Role", goal="Goal")

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s", steps={"s": {"type": "placeholder", "id": "s"}}),
        definitions={"wrong_key": agent},
    )

    errors = manifest.verify()
    if not any("Definition Key Mismatch" in e for e in errors):
        pytest.fail("verify() should detect ID mismatch")


def test_manifest_base_model_docstring() -> None:
    """
    Ensure ManifestBaseModel docstring is updated.
    """
    doc = ManifestBaseModel.__doc__
    if not doc:
        pytest.fail("Docstring is missing")
    if "dump" in doc or "to_json" in doc:
        pytest.fail("ManifestBaseModel docstring contains obsolete 'dump' or 'to_json'")


def test_generic_definition_gone() -> None:
    """
    Ensure GenericDefinition is completely removed.
    """
    with pytest.raises(ImportError):
        from coreason_manifest.spec.v2.definitions import GenericDefinition  # type: ignore[attr-defined]

    with pytest.raises(ImportError):
        from coreason_manifest.spec.v2 import GenericDefinition  # type: ignore[attr-defined] # noqa: F401


def test_all_exports_clean() -> None:
    """
    Ensure GenericDefinition is not in __all__.
    """
    import coreason_manifest.spec.v2 as v2_pkg
    from coreason_manifest.spec.v2 import definitions

    assert "GenericDefinition" not in definitions.__all__
    assert "GenericDefinition" not in v2_pkg.__all__


def test_edge_case_invalid_version_type() -> None:
    """Test invalid version type (int instead of str) causes validation error."""
    with pytest.raises(ValidationError, match="Input should be a valid string"):
        ManifestMetadata.model_validate({"name": "Test", "version": 123})


def test_edge_case_empty_name() -> None:
    """
    Test ManifestMetadata with empty name.
    (should technically pass string check, but checks strictness of required fields).
    """
    # Pydantic default min_length is not set, so empty string is valid unless constrained.
    # But missing name should fail.
    with pytest.raises(ValidationError, match="Field required"):
        ManifestMetadata.model_validate({"version": "1.0.0"})


def test_verify_skip_no_id_attribute() -> None:
    """
    Test that verify() safely skips definitions that do not have an 'id' attribute.
    (like MCPResourceDefinition).
    """
    resource = MCPResourceDefinition(
        uri="file:///tmp/test.txt",
        name="Test Resource",
    )

    # This should NOT raise AttributeError: 'MCPResourceDefinition' object has no attribute 'id'
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s", steps={"s": {"type": "placeholder", "id": "s"}}),
        definitions={"my_resource": resource},
    )

    errors = manifest.verify()
    # verify() reports placeholder steps as errors, so we ignore that one to focus on the crash check
    relevant_errors = [e for e in errors if "placeholder" not in e]
    assert len(relevant_errors) == 0


def test_complex_manifest_integrity() -> None:
    """
    Complex test case: Validating a large manifest with mixed valid and invalid definitions.
    """
    # 1. Valid Agent
    valid_agent = AgentDefinition(id="agent1", name="Valid Agent", role="R", goal="G")

    # 2. Invalid Agent (Key mismatch)
    invalid_agent = AgentDefinition(id="agent2", name="Invalid Agent", role="R", goal="G")

    # 3. Valid Resource (No ID, so skipped)
    resource = MCPResourceDefinition(uri="file:///data", name="Data")

    manifest = ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="Complex Test", version="2.0.0"),
        workflow=Workflow(start="s", steps={"s": {"type": "placeholder", "id": "s"}}),
        definitions={
            "agent1": valid_agent,  # Valid
            "wrong_key_agent": invalid_agent,  # Invalid: key != id
            "my_resource": resource,  # Valid: no ID check
        },
    )

    errors = manifest.verify()

    # Filter out placeholder step warnings
    relevant_errors = [e for e in errors if "placeholder" not in e]

    # Expect exactly 1 error for the key mismatch
    assert len(relevant_errors) == 1
    assert "Definition Key Mismatch" in relevant_errors[0]
    assert "'wrong_key_agent'" in relevant_errors[0]
    assert "'agent2'" in relevant_errors[0]
