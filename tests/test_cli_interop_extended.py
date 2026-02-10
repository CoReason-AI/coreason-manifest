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
    load_agent_from_ref(f"{p}:agent", allowed_root_dir=edge_case_dir)

    # Check if directory is NOT in sys.path (cleaned up)
    assert str(edge_case_dir) not in sys.path


def test_loader_non_agent_variable(edge_case_dir: Path) -> None:
    """Test loading a variable that is not an agent or builder."""
    p = edge_case_dir / "string_var.py"
    p.write_text("agent = 'I am just a string'")

    with pytest.raises(ValueError, match="is not a ManifestV2"):
        load_agent_from_ref(f"{p}:agent", allowed_root_dir=edge_case_dir)


def test_loader_syntax_error(edge_case_dir: Path) -> None:
    """Test loading a file with Python syntax errors."""
    p = edge_case_dir / "syntax_error.py"
    p.write_text("def broken_func(:\n    pass")

    with pytest.raises(ValueError, match="Error loading module"):
        load_agent_from_ref(f"{p}:broken_func", allowed_root_dir=edge_case_dir)


def test_loader_strict_splitting() -> None:
    """
    Test strict splitting logic.
    Format is strictly `path:var`.
    """
    # 1. Simple path
    ref = "/path/to/file.py:var"
    # rsplit(":", 1) -> "/path/to/file.py", "var" - OK

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("importlib.util.spec_from_file_location"),
        patch("coreason_manifest.utils.loader.sys.path", []),
        contextlib.suppress(Exception),
    ):  # We expect it to fail later, but check split
        # Just checking if it crashes on split
        # Use allowed_root_dir="/" to permit absolute path check during split test
        load_agent_from_ref(ref, allowed_root_dir="/")

    # 2. Windows path with drive letter AND variable
    # ref = "C:\\path\\to\\file.py:var"
    # rsplit(":", 1) -> "C:\\path\\to\\file.py", "var" - OK
    ref_win = r"C:\path\to\file.py:var"

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.stat") as mock_stat,
        patch("importlib.util.spec_from_file_location") as mock_spec_load,
    ):
        mock_stat.return_value.st_mode = 0o644
        with contextlib.suppress(Exception):
            load_agent_from_ref(ref_win)

        # Verify it resolved the correct path part (C:\path\to\file.py)
        # Note: On linux, Path("C:\...") might resolve oddly, but it should contain the path part
        args, _ = mock_spec_load.call_args
        # The path passed to spec_from_file_location should be the first part of split
        assert str(args[1]) == str(Path(r"C:\path\to\file.py").resolve())

    # 3. Path WITHOUT variable (should fail)
    # ref = "C:\\path\\to\\file.py"
    # missing colon if we ignore drive letter colon? No, rsplit(":", 1) will split at drive letter colon if present!
    # "C", "\\path\\to\\file.py".
    # file_path_str="C", var_name="\\path\\to\\file.py".
    # This is technically valid split format-wise, but "C" is likely not a file, or "\...\file.py" not a var.
    # But if "C" is a directory, Path("C").exists() might be true.
    # The requirement is strict format `path/to/file.py:variable_name`.

    ref_invalid = "/path/to/file.py"
    with pytest.raises(ValueError, match="Invalid reference format"):
        load_agent_from_ref(ref_invalid)


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
        load_agent_from_ref(f"{p}:agent", allowed_root_dir=edge_case_dir)


def test_cli_inspect_complex(complex_workflow_agent: ManifestV2, capsys: CaptureFixture[str]) -> None:
    """Verify inspect output for complex agent."""
    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=complex_workflow_agent),
        patch.object(sys, "argv", ["coreason", "inspect", "dummy.py:agent"]),
    ):
        main()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["kind"] == "Recipe"
    assert len(data["workflow"]["steps"]) == 5
    assert "AgentA" in data["definitions"]
