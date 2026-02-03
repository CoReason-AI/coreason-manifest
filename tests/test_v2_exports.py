import pytest

import coreason_manifest as cm
from coreason_manifest.v2.io import load_from_yaml
from coreason_manifest.v2.spec.definitions import ManifestV2


def test_v2_defaults() -> None:
    assert cm.Manifest is ManifestV2
    assert cm.Recipe is ManifestV2
    assert cm.load is load_from_yaml


def test_v1_removed_from_root() -> None:
    with pytest.raises(AttributeError):
        _ = cm.RecipeManifest  # type: ignore[attr-defined]

    with pytest.raises(AttributeError):
        _ = cm.AgentDefinition  # type: ignore[attr-defined]


def test_v1_fallback() -> None:
    from coreason_manifest.v1 import AgentDefinition, RecipeManifest, Topology

    assert RecipeManifest is not None
    assert AgentDefinition is not None
    assert Topology is not None


def test_v1_graph_primitives() -> None:
    from coreason_manifest.v1 import (
        AgentNode,
        ConditionalEdge,
        Edge,
        HumanNode,
        LogicNode,
        MapNode,
        RecipeNode,
        StateDefinition,
    )

    assert AgentNode is not None
    assert HumanNode is not None
    assert LogicNode is not None
    assert RecipeNode is not None
    assert MapNode is not None
    assert Edge is not None
    assert ConditionalEdge is not None
    assert StateDefinition is not None
