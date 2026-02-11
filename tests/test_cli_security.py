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
from pathlib import Path

import pytest

from coreason_manifest.utils.loader import load_agent_from_ref


@pytest.fixture
def mock_agent_file(tmp_path: Path) -> Path:
    """Create a temporary python file defining an agent."""
    file_path = tmp_path / "mock_agent.py"
    file_path.write_text(
        """
from coreason_manifest.builder import AgentBuilder
agent = AgentBuilder("MockAgent").build()
""",
        encoding="utf-8",
    )
    return file_path


def test_load_agent_security_warning(mock_agent_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that loading an agent from a file prints a security warning to stderr."""

    # We need to ensure the module can be imported, so we might need to mess with sys.path
    # but load_agent_from_ref handles sys.path insertion.

    # Force reload if it was already loaded (unlikely in fresh test, but good practice)
    module_name = mock_agent_file.stem
    if module_name in sys.modules:
        del sys.modules[module_name]

    load_agent_from_ref(f"{mock_agent_file}:agent", allowed_root_dir=mock_agent_file.parent)

    captured = capsys.readouterr()
    assert "⚠️  SECURITY WARNING: Executing code from" in captured.err
    assert str(mock_agent_file) in captured.err
