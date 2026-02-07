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
from coreason_manifest.spec.v2.definitions import (
    AgentStep,
    CouncilStep,
    LogicStep,
    ManifestMetadata,
    ManifestV2,
    SwitchStep,
    Workflow,
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


def test_loader_default_var(temp_agent_file: Path) -> None:
    # Create file with 'agent' variable
    p = temp_agent_file.parent / "default_agent.py"
    p.write_text("""
from coreason_manifest.builder import AgentBuilder
agent = AgentBuilder(name="DefaultAgent").build()
""")
    ref = str(p)
    loaded = load_agent_from_ref(ref)
    assert loaded.metadata.name == "DefaultAgent"


def test_loader_errors(temp_agent_file: Path) -> None:
    # File not found
    with pytest.raises(ValueError, match="File not found"):
        load_agent_from_ref("non_existent.py")

    # Var not found
    with pytest.raises(ValueError, match="Variable 'missing' not found"):
        load_agent_from_ref(f"{temp_agent_file}:missing")

    # Not an agent
    with pytest.raises(ValueError, match="is not a ManifestV2"):
        load_agent_from_ref(f"{temp_agent_file}:not_agent")

    # Import error (bad syntax)
    bad_file = temp_agent_file.parent / "bad.py"
    bad_file.write_text("this is not python")
    with pytest.raises(ValueError, match="Error loading module"):
        load_agent_from_ref(str(bad_file))

    # Broken builder
    with pytest.raises(ValueError, match="Error building agent"):
        load_agent_from_ref(f"{temp_agent_file}:broken_builder")

def test_loader_spec_error(temp_agent_file: Path) -> None:
    with patch("importlib.util.spec_from_file_location", return_value=None), \
         pytest.raises(ValueError, match="Could not load spec"):
        load_agent_from_ref(str(temp_agent_file))

# CLI Tests

@pytest.fixture
def mock_agent() -> ManifestV2:
    builder = AgentBuilder(name="TestAgent")
    return builder.build()


def test_cli_inspect(mock_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent), \
         patch.object(sys, "argv", ["coreason", "inspect", "dummy.py"]):
        main()

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["metadata"]["name"] == "TestAgent"
    # Verify by_alias=True (x-design vs design_metadata would be checked if present,
    # but let's check basic structure)
    assert "workflow" in output


def test_cli_viz(mock_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent), \
         patch.object(sys, "argv", ["coreason", "viz", "dummy.py"]):
        main()

    captured = capsys.readouterr()
    assert "graph TD" in captured.out


def test_cli_viz_json(mock_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent), \
         patch.object(sys, "argv", ["coreason", "viz", "dummy.py", "--json"]):
        main()

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "graph TD" in output["mermaid"]


def test_cli_run_simple(mock_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    # Add a step to mock agent
    # AgentBuilder.build() creates a default workflow with 'main' step

    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent), \
         patch.object(sys, "argv", ["coreason", "run", "dummy.py"]):
        main()

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    events = [json.loads(line) for line in lines if line.strip()]

    assert len(events) >= 2
    assert events[0]["type"] == "step_start"
    assert events[0]["step_id"] == "main"
    assert events[1]["type"] == "step_output"
    assert events[1]["output"] is None


def test_cli_run_mock(mock_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent), \
         patch("coreason_manifest.cli.generate_mock_output", return_value={"mocked": True}), \
         patch.object(sys, "argv", ["coreason", "run", "dummy.py", "--mock"]):
        main()

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    events = [json.loads(line) for line in lines if line.strip()]

    output_event = next(e for e in events if e["type"] == "step_output")
    assert output_event["output"] == {"mocked": True}


def test_cli_run_bad_inputs(mock_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent), \
         patch.object(sys, "argv", ["coreason", "run", "dummy.py", "--inputs", "{bad json"]), \
         pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    assert "Error parsing inputs" in captured.err


def test_cli_load_error(capsys: CaptureFixture[str]) -> None:
    with patch("coreason_manifest.cli.load_agent_from_ref", side_effect=ValueError("Load failed")), \
         patch.object(sys, "argv", ["coreason", "inspect", "bad.py"]), \
         pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    assert "Error loading agent: Load failed" in captured.err


# Branch coverage for run loop capabilities
def test_cli_run_capabilities(capsys: CaptureFixture[str]) -> None:
    # Construct manifest with different step types
    w = Workflow(
        start="s1",
        steps={
            "s1": LogicStep(id="s1", code="print('hi')"),
            "s2": CouncilStep(id="s2", voters=["a1"]),
            "s3": SwitchStep(id="s3", cases={"x": "s1"}),
            "s4": AgentStep(id="s4", agent="MissingAgent")  # Missing def
        }
    )
    agent = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Complex", version="1.0"),
        workflow=w,
        definitions={}
    )

    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=agent), \
         patch.object(sys, "argv", ["coreason", "run", "dummy.py", "--mock"]):
        main()

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    events = [json.loads(line) for line in lines if line.strip()]

    types = [e.get("capability") for e in events if e["type"] == "step_start"]
    assert "Logic" in types
    assert "Council" in types
    assert "Switch" in types

    # Check missing agent error
    assert "Definition for MissingAgent not found" in captured.err


def test_cli_run_mock_error(mock_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent), \
         patch("coreason_manifest.cli.generate_mock_output", side_effect=Exception("Mock fail")), \
         patch.object(sys, "argv", ["coreason", "run", "dummy.py", "--mock"]):
        main()

    captured = capsys.readouterr()
    assert "Error generating mock" in captured.err
