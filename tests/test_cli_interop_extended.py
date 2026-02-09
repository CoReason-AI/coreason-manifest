# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import contextlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from _pytest.capture import CaptureFixture

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


def test_loader_windows_path_heuristics() -> None:
    """
    Simulate loading logic for Windows paths to ensure splitting logic is robust.
    We mock Path.exists/resolve to simulate Windows environment behavior even on Linux.
    """
    # Simulate a path: C:\Users\Dev\agent.py
    # This contains a colon but is a file path, so it should NOT be split into ("C", "\Users\...")

    win_path_str = r"C:\Users\Dev\agent.py"

    # We patch Path to intercept resolving and existence checks
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.resolve", return_value=Path("/tmp/agent.py")),
        patch("coreason_manifest.utils.loader.sys.path", []),
        patch("importlib.util.spec_from_file_location") as mock_spec,
    ):
        # Mock module loading internals so it doesn't crash
        mock_module = sys.modules[__name__]  # Just use current module as dummy
        mock_spec.return_value.loader.exec_module = lambda _: None

        # We need to ensure getattr(module, "agent") returns something valid
        # But importlib returns a module. We can mock what module_from_spec returns.
        with patch("importlib.util.module_from_spec", return_value=mock_module):
            # We inject a dummy 'agent' into the mock_module (which is this test module actually)
            # But safer to mock getattr behavior if possible, or just set attribute on mock object.
            # Actually, simpler: load_agent_from_ref calls getattr(module, var_name).

            # Let's override getattr on the module object returned by module_from_spec
            patch("importlib.util.module_from_spec").start()

            # Create a dummy Manifest
            ManifestV2.model_construct(
                kind="Agent",
                metadata=ManifestMetadata(name="WinAgent", version="1.0"),
                workflow=Workflow(start="s", steps={}),
            )

            # The loader logic:
            # 1. Checks splits
            # 2. Resolves path
            # 3. Loads module
            # 4. Gets var

            # If our logic is correct, for "C:\...\agent.py", var_name should remain "agent" (default).
            # If logic is wrong, it splits to "C", and var_name becomes "\...\agent.py".

            # So we verify that the loader attempts to load from the FULL path, not "C".
            # And looks for "agent".

            # To verify this without full execution, we can rely on how `Path(file_path_str)` is called.
            # But `load_agent_from_ref` does `Path(file_path_str).resolve()`.

            # Let's spy on Path constructor? Hard.
            # Instead, we can force failure if it tries to load the wrong path.

    # Actually, simply running the splitting logic in isolation is better for a unit test of the utility
    # function, but the utility function is monolithic.
    # Let's invoke `load_agent_from_ref` and expect it to reach the file loading stage with correct path.

    with patch("pathlib.Path.exists") as mock_exists:
        # Scenario 1: Absolute path with colon (drive letter), default var
        # ref = "C:\foo.py"
        # "C:\foo.py".rsplit(":", 1) -> "C", "\foo.py"
        # "\foo.py" has "\", so heuristic should prevent split.
        # path becomes "C:\foo.py", var becomes "agent"

        mock_exists.return_value = True  # Pretend file exists

        # We expect it to try to load "C:\foo.py"
        # We'll fail at spec_from_file_location or module loading, catching that to verify args

        with patch("importlib.util.spec_from_file_location") as mock_spec_load:
            with contextlib.suppress(Exception):
                load_agent_from_ref(win_path_str)

            # Verify it tried to load the full path
            # spec_from_file_location(name, path)
            args, _ = mock_spec_load.call_args
            # The second arg is the path
            assert str(args[1]) == str(Path(win_path_str).resolve())

    with patch("pathlib.Path.exists") as mock_exists:
        # Scenario 2: Absolute path with colon AND explicit var
        # ref = "C:\foo.py:my_var"
        # rsplit -> "C:\foo.py", "my_var"
        # "my_var" has no sep. Split accepted.
        # path "C:\foo.py", var "my_var"

        mock_exists.return_value = True
        win_path_with_var = r"C:\Users\Dev\agent.py:my_custom_agent"

        with patch("importlib.util.spec_from_file_location") as mock_spec_load:
            with contextlib.suppress(Exception):
                load_agent_from_ref(win_path_with_var)

            # It should have tried to load C:\Users\Dev\agent.py
            args, _ = mock_spec_load.call_args
            expected_path = win_path_str  # The part before :
            assert str(args[1]) == str(Path(expected_path).resolve())

            # To verify var name, we'd need to mock the module loading deeper, but path correctness is the main risk.


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
    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=complex_workflow_agent),
        patch.object(sys, "argv", ["coreason", "inspect", "dummy.py"]),
    ):
        main()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["kind"] == "Recipe"
    assert len(data["workflow"]["steps"]) == 5
    assert "AgentA" in data["definitions"]
