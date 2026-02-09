import json
import sys
from unittest.mock import MagicMock, patch

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


def test_viz_recipe_not_implemented(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that 'viz' command fails for RecipeDefinition."""
    recipe = create_dummy_recipe()

    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=recipe),
        patch.object(sys, "argv", ["coreason", "viz", "dummy:recipe"]),
    ):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "Visualization not yet implemented for RecipeDefinition" in captured.err


