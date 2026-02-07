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
    AgentDefinition,
    AgentStep,
    CouncilStep,
    LogicStep,
    ManifestMetadata,
    ManifestV2,
    SwitchStep,
    Workflow,
)
from coreason_manifest.utils.loader import load_agent_from_ref

# --- Edge Cases ---

@pytest.fixture
def edge_case_dir(tmp_path: Path) -> Path:
    d = tmp_path / "edge_cases"
    d.mkdir()
    return d

def test_loader_sys_path_modification(edge_case_dir: Path) -> None:
    """Verify that the loader adds the directory to sys.path correctly."""
    p = edge_case_dir / "path_test.py"
    # Create a valid agent file to load successfully
    p.write_text("""
from coreason_manifest.builder import AgentBuilder
agent = AgentBuilder(name="PathTest").build()
""")

    # Load it
    load_agent_from_ref(str(p))

    # Check if directory is in sys.path
    assert str(edge_case_dir) in sys.path

def test_loader_non_agent_variable(edge_case_dir: Path) -> None:
    """Test loading a variable that is not an agent or builder."""
    p = edge_case_dir / "string_var.py"
    p.write_text("agent = 'I am just a string'")

    with pytest.raises(ValueError, match="is not a ManifestV2"):
        load_agent_from_ref(str(p))

def test_loader_syntax_error(edge_case_dir: Path) -> None:
    """Test loading a file with Python syntax errors."""
    p = edge_case_dir / "syntax_error.py"
    p.write_text("def broken_func(:\n    pass")

    with pytest.raises(ValueError, match="Error loading module"):
        load_agent_from_ref(str(p))

def test_cli_run_empty_inputs(capsys: CaptureFixture[str]) -> None:
    """Test running with empty JSON object inputs."""
    builder = AgentBuilder(name="EmptyInputAgent")
    agent = builder.build()

    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=agent), \
         patch.object(sys, "argv", ["coreason", "run", "dummy.py", "--inputs", "{}"]):
        main()

    captured = capsys.readouterr()
    assert "step_start" in captured.out

def test_cli_run_nested_json_inputs(capsys: CaptureFixture[str]) -> None:
    """Test running with deeply nested JSON inputs."""
    builder = AgentBuilder(name="NestedInputAgent")
    agent = builder.build()

    inputs = json.dumps({"a": {"b": {"c": [1, 2, 3]}}})

    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=agent), \
         patch.object(sys, "argv", ["coreason", "run", "dummy.py", "--inputs", inputs]):
        main()

    captured = capsys.readouterr()
    assert "step_start" in captured.out

# --- Complex Cases ---

@pytest.fixture
def complex_workflow_agent() -> ManifestV2:
    """
    Creates a manifest with a complex workflow:
    Start -> Logic -> Switch -> (Case A: Agent) -> Council -> End
                            -> (Case B: Agent) -> End
    """

    # Definitions
    agent_a_def = AgentDefinition(id="AgentA", name="AgentA", role="RoleA", goal="GoalA")
    agent_b_def = AgentDefinition(id="AgentB", name="AgentB", role="RoleB", goal="GoalB")

    # Workflow
    steps = {
        "step_logic": LogicStep(id="step_logic", code="process_data()", next="step_switch"),
        "step_switch": SwitchStep(
            id="step_switch",
            cases={"condition_a": "step_agent_a", "condition_b": "step_agent_b"},
            default="step_agent_a",
        ),
        "step_agent_a": AgentStep(id="step_agent_a", agent="AgentA", next="step_council"),
        "step_agent_b": AgentStep(id="step_agent_b", agent="AgentB", next=None),
        "step_council": CouncilStep(id="step_council", voters=["AgentA", "AgentB"], next=None),
    }

    workflow = Workflow(start="step_logic", steps=steps)

    return ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="ComplexWorkflow", version="1.0.0"),
        workflow=workflow,
        definitions={"AgentA": agent_a_def, "AgentB": agent_b_def},
    )

def test_cli_run_complex_workflow(complex_workflow_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    """
    Verify that 'run' iterates all steps in a complex workflow and emits correct events.
    Note: The CLI iteration logic simply iterates keys in definitions, not graph traversal.
    """

    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=complex_workflow_agent), \
         patch.object(sys, "argv", ["coreason", "run", "dummy.py", "--mock"]):
        main()

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    events = [json.loads(line) for line in lines if line.strip()]

    # Collect all step_ids visited
    visited_steps = [e["step_id"] for e in events if e["type"] == "step_start"]

    # Ensure all defined steps are visited (since CLI iterates dictionary)
    expected_steps = ["step_logic", "step_switch", "step_agent_a", "step_agent_b", "step_council"]
    for step in expected_steps:
        assert step in visited_steps

    # Verify Capabilities
    capabilities = {e["step_id"]: e["capability"] for e in events if e["type"] == "step_start"}
    assert capabilities["step_logic"] == "Logic"
    assert capabilities["step_switch"] == "Switch"
    assert capabilities["step_council"] == "Council"
    assert capabilities["step_agent_a"] == "AgentA"
    assert capabilities["step_agent_b"] == "AgentB"

def test_cli_run_mock_complex(complex_workflow_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    """
    Verify --mock behavior for complex workflow.
    Only AgentSteps should generate mock output.
    """
    mock_output = {"mocked_data": "test"}

    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=complex_workflow_agent), \
         patch("coreason_manifest.cli.generate_mock_output", return_value=mock_output), \
         patch.object(sys, "argv", ["coreason", "run", "dummy.py", "--mock"]):
        main()

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    events = [json.loads(line) for line in lines if line.strip()]

    # Check outputs
    outputs = {e["step_id"]: e["output"] for e in events if e["type"] == "step_output"}

    # Agent steps should have mock output
    assert outputs["step_agent_a"] == mock_output
    assert outputs["step_agent_b"] == mock_output

    # Other steps should be None (mock generation logic skips them)
    assert outputs["step_logic"] is None
    assert outputs["step_switch"] is None
    assert outputs["step_council"] is None

def test_loader_cyclic_import_simulation(edge_case_dir: Path) -> None:
    """
    Simulate a case where the imported module might raise a RecursionError during import.
    This mimics a cyclic import issue in user code.
    """
    p = edge_case_dir / "cyclic.py"
    # We can't easily create a real cyclic import with one file, but we can raise the error.
    p.write_text("""
raise RecursionError("Cyclic import detected")
""")

    with pytest.raises(ValueError, match="Error loading module"):
        load_agent_from_ref(str(p))

def test_cli_inspect_complex(complex_workflow_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    """Verify inspect output for complex agent."""
    with patch("coreason_manifest.cli.load_agent_from_ref", return_value=complex_workflow_agent), \
         patch.object(sys, "argv", ["coreason", "inspect", "dummy.py"]):
        main()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["kind"] == "Recipe"
    assert len(data["workflow"]["steps"]) == 5
    assert "AgentA" in data["definitions"]
