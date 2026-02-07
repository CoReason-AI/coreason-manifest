# Copyright (c) 2025 CoReason, Inc.

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from _pytest.capture import CaptureFixture

from coreason_manifest.cli import main
from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    ManifestMetadata,
    ManifestV2,
    Workflow,
)


@pytest.fixture
def mock_agent_def() -> AgentDefinition:
    return AgentDefinition(id="test-agent", name="TestAgent", role="Tester", goal="Testing")


@pytest.fixture
def mock_manifest(mock_agent_def: AgentDefinition) -> ManifestV2:
    return ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="TestAgent", version="1.0.0"),
        definitions={"TestAgent": mock_agent_def},
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="TestAgent")}),
    )


def test_cli_serve_mcp_success(mock_agent_def: AgentDefinition, capsys: CaptureFixture[str]) -> None:
    mock_server_instance = MagicMock()
    mock_server_instance.run_stdio = AsyncMock()

    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent_def),
        patch("coreason_manifest.cli.CoreasonMCPServer", return_value=mock_server_instance) as mock_cls,
        patch("coreason_manifest.cli.asyncio.run") as mock_run,
        patch.object(sys, "argv", ["coreason", "serve-mcp", "dummy.py:agent"]),
        patch.dict(sys.modules, {"mcp": MagicMock()}),
    ):
        main()

        mock_cls.assert_called_once()
        args, _ = mock_cls.call_args
        assert args[0] == mock_agent_def

        mock_server_instance.run_stdio.assert_called_once()
        mock_run.assert_called_once()


def test_cli_serve_mcp_missing_dependency(capsys: CaptureFixture[str]) -> None:
    # We simulate mcp missing by patching sys.modules with None for 'mcp'
    # However, since the import happens inside handle_serve_mcp, we need to make sure
    # it fails.
    # Note: cli.py has 'import mcp' inside try block.

    with (
        patch.dict(sys.modules, {"mcp": None}),
        patch.object(sys, "argv", ["coreason", "serve-mcp", "dummy.py:agent"]),
        pytest.raises(SystemExit),
    ):
        main()

    captured = capsys.readouterr()
    assert "'mcp' package is not installed" in captured.out


def test_cli_serve_mcp_manifest_extraction(mock_manifest: ManifestV2, capsys: CaptureFixture[str]) -> None:
    mock_server_instance = MagicMock()
    mock_server_instance.run_stdio = AsyncMock()

    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_manifest),
        patch("coreason_manifest.cli.CoreasonMCPServer", return_value=mock_server_instance) as mock_cls,
        patch("coreason_manifest.cli.asyncio.run"),
        patch.object(sys, "argv", ["coreason", "serve-mcp", "dummy.py:agent"]),
        patch.dict(sys.modules, {"mcp": MagicMock()}),
    ):
        main()

        mock_cls.assert_called_once()
        args, _ = mock_cls.call_args
        assert args[0].name == "TestAgent"


def test_cli_serve_mcp_extraction_error(mock_agent_def: AgentDefinition, capsys: CaptureFixture[str]) -> None:
    # Case where ManifestV2 has multiple agents or mismatch
    other_agent = AgentDefinition(id="other", name="Other", role="R", goal="G")
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="TestAgent", version="1.0.0"),
        definitions={"A1": mock_agent_def, "A2": other_agent},
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="TestAgent")}),
    )

    # This case actually succeeds because name matches, so we expect it to try to run the server.
    # We didn't mock CoreasonMCPServer here so it would try to create it.
    # But let's focus on the failing case.

    # Name mismatch scenario:
    manifest_fail = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="NoMatch", version="1.0.0"),
        definitions={"A1": mock_agent_def, "A2": other_agent},
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="TestAgent")}),
    )

    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=manifest_fail),
        patch.object(sys, "argv", ["coreason", "serve-mcp", "dummy.py:agent"]),
        patch.dict(sys.modules, {"mcp": MagicMock()}),
        pytest.raises(SystemExit),
    ):
        main()

    captured = capsys.readouterr()
    assert "Could not determine which AgentDefinition to serve" in captured.err
