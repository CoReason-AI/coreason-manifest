from pathlib import Path

from coreason_manifest import Manifest, load
from coreason_manifest.v2.adapter import v2_to_recipe
from coreason_manifest.v2.spec.definitions import (
    AgentStep,
    InterfaceDefinition,
    ManifestMetadata,
    PolicyDefinition,
    StateDefinition,
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


def test_v2_bridge_example(tmp_path: Path) -> None:
    """Replicates 'Loading and Executing a V2 Manifest' from v2_bridge.md."""

    yaml_content = """
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: My Workflow
  version: 1.0.0
interface:
  inputs: {}
  outputs: {}
state:
  schema: {}
definitions:
  gpt-4:
    type: agent
    id: gpt-4
    name: GPT-4
    role: Assistant
    goal: Help user
    model: gpt-4
workflow:
  start: step1
  steps:
    step1:
      type: agent
      id: step1
      agent: gpt-4
"""
    file_path = tmp_path / "my_workflow.v2.yaml"
    file_path.write_text(yaml_content, encoding="utf-8")

    # 1. Load V2 Manifest (Human Friendly)
    v2_manifest = load(file_path)

    # 2. Convert to V1 Recipe (Machine Optimized)
    recipe = v2_to_recipe(v2_manifest)

    # 3. Verify V1 Recipe
    assert recipe.name == "My Workflow"
    assert recipe.topology.nodes[0].id == "step1"


def test_migration_guide_v1_legacy_import() -> None:
    """Verifies that V1 legacy imports work as described in migration guide."""
    from coreason_manifest.v1 import AgentDefinition, RecipeManifest, Topology

    # Just verify they are the correct classes (implicitly checked by import success)
    assert RecipeManifest.__name__ == "RecipeManifest"
    assert AgentDefinition.__name__ == "AgentDefinition"
    assert Topology.__name__ == "GraphTopology"


def test_migration_guide_v2_standard_import() -> None:
    """Verifies V2 standard imports."""
    from coreason_manifest import Manifest, load

    assert Manifest.__name__ == "ManifestV2"
    assert callable(load)
