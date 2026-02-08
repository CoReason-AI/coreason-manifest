import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from coreason_manifest.cli import main
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphTopology,
    RecipeDefinition,
    RecipeInterface,
)


# Helper to create a dummy recipe
def create_dummy_recipe() -> RecipeDefinition:
    start_node = AgentNode(id="start", agent_ref="some-agent")
    return RecipeDefinition(
        metadata=ManifestMetadata(name="DummyRecipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=[start_node], edges=[], entry_point="start"),
    )


def test_viz_recipe_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that 'viz' command works for RecipeDefinition."""
    recipe = create_dummy_recipe()

    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=recipe),
        patch.object(sys, "argv", ["coreason", "viz", "dummy:recipe"]),
    ):
        main()

    captured = capsys.readouterr()
    assert "flowchart TD" in captured.out
    assert "Start((Start)) --> start" in captured.out


def test_run_recipe_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Test successful execution of a Recipe via CLI."""
    recipe = create_dummy_recipe()

    # Mock Executor and Trace
    mock_trace = MagicMock()
    mock_trace.trace_id = "test-trace-id"
    mock_trace.steps = ["step1", "step2"]

    # We need to mock GraphExecutor class
    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=recipe),
        patch("coreason_manifest.cli.GraphExecutor") as MockExecutor,
    ):
        instance = MockExecutor.return_value
        instance.context = {"result": "success"}
        instance.run.return_value = mock_trace  # async mock handled by asyncio.run wrapper?
        # In cli.py: trace = asyncio.run(executor.run())
        # So executor.run() must return a coroutine.

        async def async_run() -> MagicMock:
            return mock_trace

        instance.run.side_effect = async_run

        with patch.object(sys, "argv", ["coreason", "run", "dummy:recipe", "--inputs", '{"a": 1}']):
            main()

        # Check inputs passed to constructor
        MockExecutor.assert_called_with(recipe, {"a": 1})

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["trace_id"] == "test-trace-id"
    assert output["final_state"] == {"result": "success"}
    assert output["steps_count"] == 2


def test_run_recipe_exception(capsys: pytest.CaptureFixture[str]) -> None:
    """Test exception handling during Recipe execution."""
    recipe = create_dummy_recipe()

    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=recipe),
        patch("coreason_manifest.cli.GraphExecutor") as MockExecutor,
    ):
        instance = MockExecutor.return_value

        async def async_run_fail() -> None:
            raise ValueError("Graph explosion")

        instance.run.side_effect = async_run_fail

        with patch.object(sys, "argv", ["coreason", "run", "dummy:recipe"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "Error running graph executor: Graph explosion" in captured.err
