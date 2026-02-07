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
    ManifestV2, ManifestMetadata, Workflow, AgentStep, AgentDefinition, InterfaceDefinition, PolicyDefinition
)
from coreason_manifest.spec.v2.resources import ModelProfile, RateCard

agent = ManifestV2(
    kind="Agent",
    metadata=ManifestMetadata(name="MyAgent", version="1.0.0"),
    policy=PolicyDefinition(human_in_the_loop=True),
    definitions={
        "MyAgent": AgentDefinition(
            id="MyAgent",
            name="MyAgent",
            role="Assistant",
            goal="Help",
            interface=InterfaceDefinition(
                 inputs={"properties": {"query": {"type": "string"}}, "required": ["query"]}
            ),
            resources=ModelProfile(
                provider="openai",
                model_id="gpt-4",
                pricing=RateCard(input_cost=0.01, output_cost=0.01)
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
    ManifestV2, ManifestMetadata, Workflow, AgentStep, AgentDefinition, InterfaceDefinition, PolicyDefinition
)
from coreason_manifest.spec.v2.resources import ModelProfile, RateCard

agent = ManifestV2(
    kind="Agent",
    metadata=ManifestMetadata(name="MyAgent", version="1.0.0"),
    policy=PolicyDefinition(human_in_the_loop=False),  # Governance change
    definitions={
        "MyAgent": AgentDefinition(
            id="MyAgent",
            name="MyAgent",
            role="Assistant",
            goal="Help",
            interface=InterfaceDefinition(
                 inputs={"properties": {}, "required": []} # Breaking change
            ),
            resources=ModelProfile(
                provider="openai",
                model_id="gpt-4",
                pricing=RateCard(input_cost=0.02, output_cost=0.01) # Resource change
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


def test_diff_governance_resource_mixed(agent_files: tuple[Path, Path], capsys: CaptureFixture[str]) -> None:
    v1, v2 = agent_files
    with patch.object(sys, "argv", ["coreason", "diff", str(v1), str(v2)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    captured = capsys.readouterr()
    # Verify icons are present
    assert "🛡️ **GOVERNANCE**" in captured.out  # human_in_the_loop changed
    assert "💰 **RESOURCE**" in captured.out  # input_cost changed
    assert "🚨 **BREAKING**" in captured.out  # inputs changed


def test_diff_identical_refs(agent_files: tuple[Path, Path], capsys: CaptureFixture[str]) -> None:
    v1, _ = agent_files
    # Explicitly test referring to same file twice
    with patch.object(sys, "argv", ["coreason", "diff", str(v1), str(v1)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    captured = capsys.readouterr()
    assert "✅ No semantic changes detected." in captured.out


def test_diff_list_reordering(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    d = tmp_path / "lists"
    d.mkdir()

    f1 = d / "l1.py"
    f1.write_text("""
from coreason_manifest.spec.v2.definitions import (
    ManifestV2, ManifestMetadata, Workflow, AgentStep, InterfaceDefinition, AgentDefinition
)
agent = ManifestV2(
    kind="Agent",
    metadata=ManifestMetadata(name="A", version="1"),
    interface=InterfaceDefinition(),
    definitions={
        "A": AgentDefinition(id="A", name="A", role="X", goal="Y", knowledge=["a", "b"])
    },
    workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="A")})
)
""")

    f2 = d / "l2.py"
    f2.write_text("""
from coreason_manifest.spec.v2.definitions import (
    ManifestV2, ManifestMetadata, Workflow, AgentStep, InterfaceDefinition, AgentDefinition
)
agent = ManifestV2(
    kind="Agent",
    metadata=ManifestMetadata(name="A", version="1"),
    interface=InterfaceDefinition(),
    definitions={
        "A": AgentDefinition(id="A", name="A", role="X", goal="Y", knowledge=["b", "a"])
    },
    workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="A")})
)
""")

    with patch.object(sys, "argv", ["coreason", "diff", str(f1), str(f2)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    captured = capsys.readouterr()
    # definitions.A.knowledge.0: a -> b
    assert "definitions.A.knowledge.0" in captured.out
    assert "definitions.A.knowledge.1" in captured.out
