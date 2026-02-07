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
from coreason_manifest.spec.v2.contracts import InterfaceDefinition


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


def test_cli_serve_mcp_not_an_agent(capsys: CaptureFixture[str]) -> None:
    # Case where reference loads something that is neither AgentDefinition nor ManifestV2
    not_agent = "I am just a string"

    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=not_agent),
        patch.object(sys, "argv", ["coreason", "serve-mcp", "dummy.py:agent"]),
        patch.dict(sys.modules, {"mcp": MagicMock()}),
        pytest.raises(SystemExit),
    ):
        main()

    captured = capsys.readouterr()
    assert "is not an AgentDefinition" in captured.err


def test_cli_serve_mcp_import_error_mcp_in_constructor(mock_agent_def: AgentDefinition, capsys: CaptureFixture[str]) -> None:
    # Simulate CoreasonMCPServer raising ImportError (e.g. if partial mcp install)
    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent_def),
        patch("coreason_manifest.cli.CoreasonMCPServer", side_effect=ImportError("Failed init")),
        patch.object(sys, "argv", ["coreason", "serve-mcp", "dummy.py:agent"]),
        patch.dict(sys.modules, {"mcp": MagicMock()}),
        pytest.raises(SystemExit),
    ):
        main()

    captured = capsys.readouterr()
    assert "Error: Failed init" in captured.err


def test_cli_serve_mcp_runtime_error(mock_agent_def: AgentDefinition, capsys: CaptureFixture[str]) -> None:
    # Simulate runtime exception during server execution
    mock_server_instance = MagicMock()
    mock_server_instance.run_stdio = AsyncMock(side_effect=RuntimeError("Server crashed"))

    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=mock_agent_def),
        patch("coreason_manifest.cli.CoreasonMCPServer", return_value=mock_server_instance),
        patch("coreason_manifest.cli.asyncio.run", side_effect=RuntimeError("Server crashed")),
        patch.object(sys, "argv", ["coreason", "serve-mcp", "dummy.py:agent"]),
        patch.dict(sys.modules, {"mcp": MagicMock()}),
        pytest.raises(SystemExit),
    ):
        main()

    captured = capsys.readouterr()
    assert "Error running MCP server: Server crashed" in captured.err


# Complex Case: Complex Schema Interaction
@pytest.mark.asyncio
async def test_complex_schema_runner_callback(mock_agent_def: AgentDefinition) -> None:
    # Define a complex agent
    schema = {
        "type": "object",
        "properties": {
            "result": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}, "val": {"type": "string"}}
                }
            }
        }
    }
    complex_agent = AgentDefinition(
        id="complex",
        name="Complex",
        role="R",
        goal="G",
        interface=InterfaceDefinition(outputs=schema)
    )

    # We want to verify that the runner_callback created inside handle_serve_mcp
    # correctly generates mock output for this schema.
    # Since handle_serve_mcp is CLI logic, we can't easily extract the inner function.
    # Instead, we mock CoreasonMCPServer to capture the callback passed to it,
    # and then execute that callback.

    mock_server_cls = MagicMock()

    with (
        patch("coreason_manifest.cli.load_agent_from_ref", return_value=complex_agent),
        patch("coreason_manifest.cli.CoreasonMCPServer", mock_server_cls),
        patch("coreason_manifest.cli.asyncio.run"),
        patch.object(sys, "argv", ["coreason", "serve-mcp", "dummy.py:agent"]),
        patch.dict(sys.modules, {"mcp": MagicMock()}),
    ):
        main()

        # Get the callback passed to constructor
        args, _ = mock_server_cls.call_args
        callback = args[1]

        # Execute callback
        result = await callback({})

        # Verify result structure
        assert "result" in result
        assert isinstance(result["result"], list)
        if len(result["result"]) > 0:
            item = result["result"][0]
            assert "id" in item
            assert "val" in item


def test_cli_serve_mcp_load_error(capsys: CaptureFixture[str]) -> None:
    with (
        patch("coreason_manifest.cli.load_agent_from_ref", side_effect=ValueError("Load failed")),
        patch.object(sys, "argv", ["coreason", "serve-mcp", "bad.py:agent"]),
        patch.dict(sys.modules, {"mcp": MagicMock()}),
        pytest.raises(SystemExit),
    ):
        main()

    captured = capsys.readouterr()
    assert "Error loading agent: Load failed" in captured.err
