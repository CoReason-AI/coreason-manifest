# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from _pytest.capture import CaptureFixture

from coreason_manifest.builder import AgentBuilder
from coreason_manifest.cli import main
from coreason_manifest.spec.common.error import (
    AgentDefinitionError,
    AgentNotFoundError,
    InvalidReferenceError,
)
from coreason_manifest.spec.v2.definitions import (
    ManifestV2,
)
from coreason_manifest.utils.loader import load_agent_from_ref


# Helper to create temporary python file
@pytest.fixture
def temp_agent_file(tmp_path: Path) -> Path:
    d = tmp_path / "agents"
    d.mkdir()
    p = d / "my_agent.py"
    p.write_text("""
from coreason_manifest.builder import AgentBuilder
from coreason_manifest.spec.v2.definitions import (
    ManifestV2, AgentDefinition, Workflow, AgentStep, InterfaceDefinition, ManifestMetadata
)

# 1. AgentBuilder instance
builder = AgentBuilder(name="BuilderAgent")
builder_agent = builder

# 2. ManifestV2 instance
agent_def = builder.build_definition()
manifest = ManifestV2(
    kind="Agent",
    metadata=ManifestMetadata(name="ManifestAgent", version="1.0.0"),
    interface=InterfaceDefinition(),
    definitions={"BuilderAgent": agent_def},
    workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="BuilderAgent")})
)

# 3. Not an agent
not_agent = "I am a string"

# 4. Broken Builder
class BrokenBuilder(AgentBuilder):
    def build(self):
        raise RuntimeError("Build failed")

broken_builder = BrokenBuilder(name="Broken")
""")
    return p


def test_loader_manifest(temp_agent_file: Path) -> None:
    ref = f"{temp_agent_file}:manifest"
    agent = load_agent_from_ref(ref)
    assert isinstance(agent, ManifestV2)
    assert agent.metadata.name == "ManifestAgent"


def test_loader_builder(temp_agent_file: Path) -> None:
    ref = f"{temp_agent_file}:builder_agent"
    agent = load_agent_from_ref(ref)
    assert isinstance(agent, ManifestV2)
    assert agent.metadata.name == "BuilderAgent"


def test_loader_missing_colon_error(temp_agent_file: Path) -> None:
    """Test that missing colon raises InvalidReferenceError."""
    # Use a string that definitely has no colon to test the format check across all platforms
    with pytest.raises(InvalidReferenceError, match="Invalid reference format"):
        load_agent_from_ref("path/to/file.py")

    # Test empty path or variable
    with pytest.raises(InvalidReferenceError, match="Reference must contain both"):
        load_agent_from_ref(":agent")

    with pytest.raises(InvalidReferenceError, match="Reference must contain both"):
        load_agent_from_ref(f"{temp_agent_file}:")


def test_loader_errors(temp_agent_file: Path) -> None:
    # File not found
    with pytest.raises(AgentNotFoundError, match="File not found"):
        load_agent_from_ref("non_existent.py:agent")

    # Var not found
    with pytest.raises(AgentDefinitionError, match="Variable 'missing' not found"):
        load_agent_from_ref(f"{temp_agent_file}:missing")

    # Not an agent
    with pytest.raises(AgentDefinitionError, match="is not a ManifestV2"):
        load_agent_from_ref(f"{temp_agent_file}:not_agent")

    # Import error (bad syntax)
    bad_file = temp_agent_file.parent / "bad.py"
    bad_file.write_text("class 123:")
    with pytest.raises(AgentDefinitionError, match="Failed to import module"):
        load_agent_from_ref(f"{bad_file}:agent")

    # Broken builder
    with pytest.raises(AgentDefinitionError, match="Error building agent"):
        load_agent_from_ref(f"{temp_agent_file}:broken_builder")


def test_loader_spec_error(temp_agent_file: Path) -> None:
    with (
        patch("importlib.util.spec_from_file_location", return_value=None),
        pytest.raises(AgentDefinitionError, match="Could not load spec"),
    ):
        load_agent_from_ref(f"{temp_agent_file}:agent")


# CLI Tests


@pytest.fixture
def mock_agent() -> ManifestV2:
    builder = AgentBuilder(name="TestAgent")
    return builder.build()


def test_cli_inspect(mock_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent),
        patch.object(sys, "argv", ["coreason", "inspect", "dummy.py:agent"]),
    ):
        main()

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["metadata"]["name"] == "TestAgent"
    # Verify by_alias=True (x-design vs design_metadata would be checked if present,
    # but let's check basic structure)
    assert "workflow" in output


def test_cli_viz(mock_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent),
        patch.object(sys, "argv", ["coreason", "viz", "dummy.py:agent"]),
    ):
        main()

    captured = capsys.readouterr()
    assert "graph TD" in captured.out


def test_cli_viz_json(mock_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent),
        patch.object(sys, "argv", ["coreason", "viz", "dummy.py:agent", "--json"]),
    ):
        main()

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "graph TD" in output["mermaid"]


def test_cli_load_error(capsys: CaptureFixture[str]) -> None:
    with (
        patch("coreason_manifest.cli.load_agent_from_ref", side_effect=AgentDefinitionError("Load failed")),
        patch.object(sys, "argv", ["coreason", "inspect", "bad.py:agent"]),
        pytest.raises(SystemExit),
    ):
        main()

    captured = capsys.readouterr()
    assert "Error loading agent: Load failed" in captured.err
