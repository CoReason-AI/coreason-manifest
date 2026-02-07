import json
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from _pytest.capture import CaptureFixture

from coreason_manifest.cli import main

# Helper to create a valid agent file
def create_agent_file(path: Path, name: str = "TestAgent", description: str = "A test agent") -> Path:
    content = f"""
from coreason_manifest.builder import AgentBuilder
builder = AgentBuilder(name="{name}")
builder.with_system_prompt("{description}")
agent = builder.build()
"""
    path.write_text(content)
    return path

def test_hash_determinism(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    agent_file = tmp_path / "agent.py"
    create_agent_file(agent_file)

    # Run 1
    with patch.object(sys, "argv", ["coreason", "hash", str(agent_file)]):
        main()
    hash1 = capsys.readouterr().out.strip()

    # Run 2
    with patch.object(sys, "argv", ["coreason", "hash", str(agent_file)]):
        main()
    hash2 = capsys.readouterr().out.strip()

    assert hash1 == hash2
    assert hash1.startswith("sha256:")

def test_hash_sensitivity(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    file1 = tmp_path / "agent1.py"
    create_agent_file(file1, description="Version 1")

    file2 = tmp_path / "agent2.py"
    create_agent_file(file2, description="Version 2")

    with patch.object(sys, "argv", ["coreason", "hash", str(file1)]):
        main()
    hash1 = capsys.readouterr().out.strip()

    with patch.object(sys, "argv", ["coreason", "hash", str(file2)]):
        main()
    hash2 = capsys.readouterr().out.strip()

    assert hash1 != hash2

def test_hash_json_output(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    agent_file = tmp_path / "agent.py"
    create_agent_file(agent_file)

    with patch.object(sys, "argv", ["coreason", "hash", str(agent_file), "--json"]):
        main()

    output = capsys.readouterr().out.strip()
    data = json.loads(output)

    assert "hash" in data
    assert data["hash"].startswith("sha256:")
    assert data["algorithm"] == "sha256"

def test_hash_capability_check(capsys: CaptureFixture[str]) -> None:
    with patch("coreason_manifest.cli.load_agent_from_ref") as mock_load:
        class BadAgent:
            pass

        mock_load.return_value = BadAgent()

        with patch.object(sys, "argv", ["coreason", "hash", "dummy.py"]):
            with pytest.raises(SystemExit) as excinfo:
                main()

        assert excinfo.value.code == 1
        assert "does not support canonical hashing" in capsys.readouterr().err
