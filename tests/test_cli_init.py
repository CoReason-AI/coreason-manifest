import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from coreason_manifest.cli import main
from coreason_manifest.spec.v2.definitions import AgentDefinition
from coreason_manifest.utils.loader import load_agent_from_ref


def test_init_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test successful creation of a new agent project."""
    project_name = "my_new_agent"
    project_dir = tmp_path / project_name

    # Simulate CLI execution
    with patch.object(sys, "argv", ["coreason", "init", str(project_dir)]):
        main()

    # Verify directory structure
    assert project_dir.exists()
    assert (project_dir / ".vscode").exists()
    assert (project_dir / "agent.py").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / ".gitignore").exists()
    assert (project_dir / ".vscode" / "launch.json").exists()

    # Check output
    captured = capsys.readouterr()
    assert (
        f"Created new agent project in '{project_dir}'" in captured.out
        or f"Created new agent project in './{project_dir}'" in captured.out
    )

    # Verify generated python code is valid and loadable
    ref = f"{project_dir}/agent.py:agent"

    # We need to make sure the load_agent_from_ref can import the module.
    # It dynamically imports, so it should work if the file exists.
    agent = load_agent_from_ref(ref)

    assert agent.metadata.name == "GreeterAgent"
    assert "GreeterAgent" in agent.definitions

    # Check RateCard resources
    greeter_def = agent.definitions["GreeterAgent"]
    # Mypy narrowing
    assert isinstance(greeter_def, AgentDefinition)
    assert greeter_def.resources is not None
    assert greeter_def.resources.pricing is not None
    assert greeter_def.resources.pricing.input_cost == 0.03


def test_init_safety_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that init aborts if directory exists and is not empty."""
    project_name = "existing_agent"
    project_dir = tmp_path / project_name
    project_dir.mkdir()
    (project_dir / "some_file.txt").write_text("content")

    with patch.object(sys, "argv", ["coreason", "init", str(project_dir)]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    captured = capsys.readouterr()
    # output might be captured in stdout
    assert (
        f"Error: Directory '{project_name}' is not empty." in captured.out
        or f"Error: Directory '{project_dir}' is not empty." in captured.out
    )


def test_init_existing_empty_dir(tmp_path: Path) -> None:
    """Test that init proceeds if directory exists but is empty."""
    project_name = "empty_agent"
    project_dir = tmp_path / project_name
    project_dir.mkdir()

    with patch.object(sys, "argv", ["coreason", "init", str(project_dir)]):
        main()

    assert (project_dir / "agent.py").exists()
