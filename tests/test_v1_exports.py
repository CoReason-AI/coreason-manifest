# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.topology import (
    AgentNode,
    ConditionalEdge,
    Edge,
    GraphTopology,
    HumanNode,
    LogicNode,
    MapNode,
    RecipeNode,
    StateDefinition,
)
from coreason_manifest.recipes import RecipeManifest
from coreason_manifest.v1 import (
    Agent,
    Recipe,
    Topology,
)
from coreason_manifest.v1 import (
    AgentDefinition as AgentDef,
)
from coreason_manifest.v1 import (
    AgentNode as AgentNodeV1,
)
from coreason_manifest.v1 import (
    ConditionalEdge as ConditionalEdgeV1,
)
from coreason_manifest.v1 import (
    Edge as EdgeV1,
)
from coreason_manifest.v1 import (
    GraphTopology as GraphTopologyV1,
)
from coreason_manifest.v1 import (
    HumanNode as HumanNodeV1,
)
from coreason_manifest.v1 import (
    LogicNode as LogicNodeV1,
)
from coreason_manifest.v1 import (
    MapNode as MapNodeV1,
)
from coreason_manifest.v1 import (
    RecipeManifest as RecipeManifestV1,
)
from coreason_manifest.v1 import (
    RecipeNode as RecipeNodeV1,
)
from coreason_manifest.v1 import (
    StateDefinition as StateDefinitionV1,
)


def test_v1_imports() -> None:
    """Verify v1 imports point to correct classes."""
    # Aliases
    assert Agent is AgentDefinition
    assert Recipe is RecipeManifest
    assert Topology is GraphTopology

    # Direct re-exports (Testing coverage for all exports)
    assert AgentDef is AgentDefinition
    assert RecipeManifestV1 is RecipeManifest
    assert GraphTopologyV1 is GraphTopology
    assert AgentNodeV1 is AgentNode
    assert HumanNodeV1 is HumanNode
    assert LogicNodeV1 is LogicNode
    assert MapNodeV1 is MapNode
    assert RecipeNodeV1 is RecipeNode
    assert EdgeV1 is Edge
    assert ConditionalEdgeV1 is ConditionalEdge
    assert StateDefinitionV1 is StateDefinition
