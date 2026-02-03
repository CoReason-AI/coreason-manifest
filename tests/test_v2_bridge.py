# Copyright (c) 2025 CoReason, Inc.

from pathlib import Path

import pytest

from coreason_manifest.definitions.topology import (
    AgentNode,
    ConditionalEdge,
    Edge,
    GraphTopology,
    LogicNode,
)
from coreason_manifest.recipes import RecipeManifest
from coreason_manifest.v2.adapter import v2_to_recipe
from coreason_manifest.v2.compiler import compile_to_topology
from coreason_manifest.v2.io import dump_to_yaml, load_from_yaml
from coreason_manifest.v2.spec.definitions import (
    AgentStep,
    ManifestMetadata,
    ManifestV2,
    Workflow,
)

SAMPLE_V2_YAML = """
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "Test Recipe"
  x-design:
    x: 100
    y: 200
    icon: "test-icon"
workflow:
  start: "step1"
  steps:
    step1:
      type: "agent"
      id: "step1"
      agent: "coreason.agent.v1"
      inputs:
        foo: "bar"
      next: "step2"
    step2:
      type: "switch"
      id: "step2"
      cases:
        "x > 10": "step3"
        "x <= 10": "step4"
      default: "step4"
    step3:
      type: "logic"
      id: "step3"
      code: "print('hello')"
    step4:
      type: "council"
      id: "step4"
      voters: ["agent1", "agent2"]
      strategy: "consensus"
"""


def test_load_from_yaml(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(SAMPLE_V2_YAML, encoding="utf-8")

    manifest = load_from_yaml(f)
    assert isinstance(manifest, ManifestV2)
    assert manifest.metadata.name == "Test Recipe"
    assert len(manifest.workflow.steps) == 4

    # Check design metadata alias
    assert manifest.metadata.design_metadata is not None
    assert manifest.metadata.design_metadata.icon == "test-icon"


def test_compile_to_topology(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(SAMPLE_V2_YAML, encoding="utf-8")
    manifest = load_from_yaml(f)

    topology = compile_to_topology(manifest)
    assert isinstance(topology, GraphTopology)

    # Nodes
    assert len(topology.nodes) == 4
    node_map = {n.id: n for n in topology.nodes}

    # Check AgentNode
    assert isinstance(node_map["step1"], AgentNode)
    assert node_map["step1"].agent_name == "coreason.agent.v1"
    assert node_map["step1"].config == {"foo": "bar"}

    # Check SwitchNode (LogicNode)
    assert isinstance(node_map["step2"], LogicNode)
    assert "def switch_logic" in node_map["step2"].code

    # Check CouncilNode (LogicNode)
    assert isinstance(node_map["step4"], LogicNode)
    assert node_map["step4"].council_config is not None
    assert node_map["step4"].council_config.voters == ["agent1", "agent2"]

    # Edges
    # step1 -> step2 (Edge)
    # step2 -> step3/step4 (ConditionalEdge)
    # step3 -> None
    # step4 -> None

    edges = topology.edges
    assert len(edges) == 2  # 1 Edge + 1 ConditionalEdge

    edge1 = next((e for e in edges if e.source_node_id == "step1"), None)
    assert isinstance(edge1, Edge)
    assert edge1.target_node_id == "step2"

    edge2 = next((e for e in edges if e.source_node_id == "step2"), None)
    assert isinstance(edge2, ConditionalEdge)
    assert "case_0" in edge2.mapping
    assert edge2.mapping["case_0"] == "step3"
    assert edge2.mapping["default"] == "step4"


def test_dangling_pointer() -> None:
    manifest = ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="Bad"),
        workflow=Workflow(
            start="step1",
            steps={"step1": AgentStep(id="step1", agent="a", next="step_non_existent")},
        ),
    )

    with pytest.raises(ValueError, match="references non-existent step"):
        compile_to_topology(manifest)


def test_v2_to_recipe(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(SAMPLE_V2_YAML, encoding="utf-8")
    manifest = load_from_yaml(f)

    recipe = v2_to_recipe(manifest)
    assert isinstance(recipe, RecipeManifest)
    assert recipe.name == "Test Recipe"
    assert recipe.version == "0.1.0"
    assert len(recipe.topology.nodes) == 4


def test_dump_to_yaml() -> None:
    manifest = ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s1", steps={}),
    )

    s = dump_to_yaml(manifest)
    # Basic check for ordering
    # Check that apiVersion appears before workflow
    assert s.index("apiVersion") < s.index("workflow")
    assert s.index("kind") < s.index("workflow")
