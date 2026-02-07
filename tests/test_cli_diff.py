import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from _pytest.capture import CaptureFixture

from coreason_manifest.cli import main


@pytest.fixture
def agent_files(tmp_path: Path) -> tuple[Path, Path]:
    d = tmp_path / "agents"
    d.mkdir()

    # Base agent (v1)
    v1 = d / "v1.py"
    v1.write_text("""
from coreason_manifest.spec.v2.definitions import (
    ManifestV2, ManifestMetadata, Workflow, AgentStep, AgentDefinition, InterfaceDefinition
)

agent = ManifestV2(
    kind="Agent",
    metadata=ManifestMetadata(name="MyAgent", version="1.0.0"),
    interface=InterfaceDefinition(
        inputs={"properties": {"query": {"type": "string"}}, "required": ["query"]}
    ),
    definitions={
        "MyAgent": AgentDefinition(
            id="MyAgent",
            name="MyAgent",
            role="Assistant",
            goal="Help",
            interface=InterfaceDefinition(
                 inputs={"properties": {"query": {"type": "string"}}, "required": ["query"]}
            )
        )
    },
    workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="MyAgent")})
)
""")

    # Head agent (v2) - Breaking change: removed 'query' input
    v2 = d / "v2.py"
    v2.write_text("""
from coreason_manifest.spec.v2.definitions import (
    ManifestV2, ManifestMetadata, Workflow, AgentStep, AgentDefinition, InterfaceDefinition
)

agent = ManifestV2(
    kind="Agent",
    metadata=ManifestMetadata(name="MyAgent", version="1.0.0"),
    interface=InterfaceDefinition(
        inputs={"properties": {}, "required": []}
    ),
    definitions={
        "MyAgent": AgentDefinition(
            id="MyAgent",
            name="MyAgent",
            role="Assistant",
            goal="Help",
            interface=InterfaceDefinition(
                 inputs={"properties": {}, "required": []}
            )
        )
    },
    workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="MyAgent")})
)
""")
    return v1, v2


def test_diff_no_changes(agent_files: tuple[Path, Path], capsys: CaptureFixture[str]) -> None:
    v1, _ = agent_files
    # Compare v1 against v1
    with patch.object(sys, "argv", ["coreason", "diff", str(v1), str(v1)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    captured = capsys.readouterr()
    assert "✅ No semantic changes detected." in captured.out


def test_diff_breaking_changes(agent_files: tuple[Path, Path], capsys: CaptureFixture[str]) -> None:
    v1, v2 = agent_files
    # Compare v1 against v2
    with patch.object(sys, "argv", ["coreason", "diff", str(v1), str(v2)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0  # Default is success even with changes

    captured = capsys.readouterr()
    # Expect breaking change icon
    assert "🚨 **BREAKING**" in captured.out
    # The path in diff is interface.inputs.properties.query
    assert "interface.inputs.properties.query" in captured.out


def test_diff_fail_on_breaking(agent_files: tuple[Path, Path], capsys: CaptureFixture[str]) -> None:
    v1, v2 = agent_files
    # Compare v1 against v2 with flag
    with patch.object(sys, "argv", ["coreason", "diff", str(v1), str(v2), "--fail-on-breaking"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2

    captured = capsys.readouterr()
    assert "❌ Blocking CI due to breaking changes." in captured.err


def test_diff_json_output(agent_files: tuple[Path, Path], capsys: CaptureFixture[str]) -> None:
    v1, v2 = agent_files
    with patch.object(sys, "argv", ["coreason", "diff", str(v1), str(v2), "--json"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "changes" in data
    assert any(c["category"] == "BREAKING" for c in data["changes"])


def test_diff_load_error(capsys: CaptureFixture[str]) -> None:
    with patch.object(sys, "argv", ["coreason", "diff", "nonexistent.py", "nonexistent.py"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

    captured = capsys.readouterr()
    assert "Error loading agent" in captured.err
