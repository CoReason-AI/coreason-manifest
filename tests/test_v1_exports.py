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
from coreason_manifest.definitions.topology import GraphTopology
from coreason_manifest.recipes import RecipeManifest
from coreason_manifest.v1 import Agent, Recipe, Topology


def test_v1_imports() -> None:
    """Verify v1 imports point to correct classes."""
    assert Agent is AgentDefinition
    assert Recipe is RecipeManifest
    assert Topology is GraphTopology
