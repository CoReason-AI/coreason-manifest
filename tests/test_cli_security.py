import sys
from pathlib import Path
from typing import Generator

import pytest
from pytest import CaptureFixture

from coreason_manifest.utils.loader import load_agent_from_ref


@pytest.fixture
def mock_agent_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary python file defining an agent."""
    file_path = tmp_path / "mock_agent.py"
    file_path.write_text(
        """
from coreason_manifest.builder import AgentBuilder
agent = AgentBuilder("MockAgent").build()
""",
        encoding="utf-8",
    )
    yield file_path


def test_load_agent_security_warning(mock_agent_file: Path, capsys: CaptureFixture[str]) -> None:
    """Test that loading an agent from a file prints a security warning to stderr."""

    # We need to ensure the module can be imported, so we might need to mess with sys.path
    # but load_agent_from_ref handles sys.path insertion.

    # Force reload if it was already loaded (unlikely in fresh test, but good practice)
    module_name = mock_agent_file.stem
    if module_name in sys.modules:
        del sys.modules[module_name]

    load_agent_from_ref(f"{mock_agent_file}:agent")

    captured = capsys.readouterr()
    assert "⚠️  SECURITY WARNING: Executing code from" in captured.err
    assert str(mock_agent_file) in captured.err
