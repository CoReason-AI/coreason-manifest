# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import sys
from unittest.mock import patch

import pytest

from coreason_manifest.cli import main
from coreason_manifest.spec.common.presentation import NodePresentation
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphTopology,
    RecipeDefinition,
    RecipeInterface,
)


# Helper to create a dummy recipe
def create_dummy_recipe() -> RecipeDefinition:
    start_node = AgentNode(id="start", agent_ref="some-agent", presentation=NodePresentation(x=0, y=0))
    return RecipeDefinition(
        metadata=ManifestMetadata(name="DummyRecipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=[start_node], edges=[], entry_point="start"),
    )


def test_viz_recipe_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that 'viz' command succeeds for RecipeDefinition."""
    recipe = create_dummy_recipe()

    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=recipe),
        patch.object(sys, "argv", ["coreason", "viz", "dummy:recipe"]),
    ):
        main()

    captured = capsys.readouterr()
    # Check for Mermaid graph start
    assert "graph TD" in captured.out
    # Check for the node
    assert "start" in captured.out
