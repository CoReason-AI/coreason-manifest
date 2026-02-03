from coreason_manifest import Manifest
from coreason_manifest.v2.spec.contracts import (
    InterfaceDefinition,
    PolicyDefinition,
    StateDefinition,
)
from coreason_manifest.v2.spec.definitions import (
    AgentStep,
    ManifestMetadata,
    Workflow,
)


def test_usage_guide_programmatic_creation() -> None:
    """Replicates the 'Creating a Manifest Programmatically' example from usage.md."""
    # 1. Define Metadata
    metadata = ManifestMetadata(name="Research Agent", version="1.0.0")

    # 2. Define Workflow
    workflow = Workflow(
        start="step1",
        steps={
            "step1": AgentStep(id="step1", agent="gpt-4-researcher", next="step2"),
            # Mock step2 to satisfy integrity
            "step2": AgentStep(id="step2", agent="summarizer"),
        },
    )

    # 3. Instantiate Manifest
    # Note: 'Recipe' is an alias for ManifestV2 in root
    manifest = Manifest(
        kind="Recipe",
        metadata=metadata,
        interface=InterfaceDefinition(inputs={"topic": {"type": "string"}}, outputs={"summary": {"type": "string"}}),
        state=StateDefinition(),
        policy=PolicyDefinition(max_retries=3),
        workflow=workflow,
    )

    assert manifest.metadata.name == "Research Agent"
    assert manifest.workflow.start == "step1"


def test_usage_guide_mutable_fields() -> None:
    """Replicates 'Accessing Fields' example from usage.md."""
    manifest = Manifest(
        kind="Recipe",
        metadata=ManifestMetadata(name="Test", version="1.0.0"),
        interface=InterfaceDefinition(inputs={"topic": {"type": "string"}}, outputs={}),
        state=StateDefinition(),
        workflow=Workflow(start="s1", steps={"s1": AgentStep(id="s1", agent="a")}),
    )

    # Reading is allowed
    assert manifest.interface.inputs["topic"]["type"] == "string"

    # Writing is allowed (V2 Manifests are mutable for ease of authoring)
    manifest.interface.inputs["topic"] = {"type": "integer"}
    assert manifest.interface.inputs["topic"]["type"] == "integer"


def test_migration_guide_v2_standard_import() -> None:
    """Verifies V2 standard imports."""
    from coreason_manifest import Manifest, load

    assert Manifest.__name__ == "ManifestV2"
    assert callable(load)
