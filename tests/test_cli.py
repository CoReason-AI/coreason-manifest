import json
from pathlib import Path
from unittest.mock import patch

import pytest

from coreason_manifest.cli.export import main as export_main
from coreason_manifest.cli.mcp_server import get_schema, list_schemas
from coreason_manifest.cli.visualize import main as visualize_main
from coreason_manifest.cli.validate import main as validate_main


def test_export_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    export_main()
    assert (tmp_path / "coreason_ontology.schema.json").exists()


def test_mcp_server_schemas() -> None:
    schemas = list_schemas()
    assert len(schemas) > 0
    assert "WorkflowEnvelope" in schemas

    schema = get_schema("WorkflowEnvelope")
    assert schema["title"] == "WorkflowEnvelope"

    with pytest.raises(ValueError, match="Schema 'NonExistentSchema' not found"):
        get_schema("NonExistentSchema")


def test_visualize_valid_manifest(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload_path = tmp_path / "valid_manifest.json"
    manifest_data = {
        "manifest_id": "manifest-test-01",
        "artifact_profile": {
            "artifact_event_id": "root-artifact",
            "detected_modalities": ["text", "tabular_grid"],
            "token_density": 100,
        },
        "active_subgraphs": {"text": ["did:web:agent-1"]},
        "bypassed_steps": [
            {
                "artifact_event_id": "root-artifact",
                "bypassed_node_id": "did:web:agent-2",
                "justification": "modality_mismatch",
                "cryptographic_null_hash": "a" * 64,
            }
        ],
        "branch_budgets_microcents": {"did:web:agent-1": 1000},
    }
    payload_path.write_text(json.dumps(manifest_data))

    with (
        patch("sys.argv", ["coreason-visualize", str(payload_path)]),
        patch("sys.exit", side_effect=SystemExit) as mock_exit,
    ):
        with pytest.raises(SystemExit):
            visualize_main()
        mock_exit.assert_called_once_with(0)

    captured = capsys.readouterr()
    assert "graph TD" in captured.out
    assert "did:web:agent-1" in captured.out
    assert "did:web:agent-2" in captured.out
    assert ":::active" in captured.out
    assert ":::bypassed" in captured.out


def test_visualize_invalid_manifest(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload_path = tmp_path / "invalid_manifest.json"
    payload_path.write_text('{"invalid": "data"}')

    with (
        patch("sys.argv", ["coreason-visualize", str(payload_path)]),
        patch("sys.exit", side_effect=SystemExit) as mock_exit,
    ):
        with pytest.raises(SystemExit):
            visualize_main()
        mock_exit.assert_called_once_with(1)

    captured = capsys.readouterr()
    assert "Topological Validation Error" in captured.err


def test_visualize_missing_file(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("sys.argv", ["coreason-visualize", "ghost_file.json"]),
        patch("sys.exit", side_effect=SystemExit) as mock_exit,
    ):
        with pytest.raises(SystemExit):
            visualize_main()
        mock_exit.assert_called_once_with(1)

    captured = capsys.readouterr()
    assert "not found" in captured.err
def test_validate_cli_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = {"description": "A valid system node", "type": "system"}
    payload_file = tmp_path / "valid.json"
    payload_file.write_text(json.dumps(payload))

    monkeypatch.setattr("sys.argv", ["coreason-validate", "--schema=SystemNode", str(payload_file)])

    with pytest.raises(SystemExit) as exc_info:
        validate_main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_validate_cli_invalid_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload_file = tmp_path / "dummy.json"
    payload_file.write_text("{}")

    monkeypatch.setattr("sys.argv", ["coreason-validate", "--schema=GhostSchema", str(payload_file)])

    with pytest.raises(SystemExit) as exc_info:
        validate_main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Schema 'GhostSchema' not found" in captured.err


def test_validate_cli_structural_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = {"invalid_field": "This will fail SystemNode strict validation"}
    payload_file = tmp_path / "invalid.json"
    payload_file.write_text(json.dumps(payload))

    monkeypatch.setattr("sys.argv", ["coreason-validate", "--schema=SystemNode", str(payload_file)])

    with pytest.raises(SystemExit) as exc_info:
        validate_main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "validation error" in captured.err.lower()


def test_validate_cli_missing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    missing_file = tmp_path / "missing.json"
    monkeypatch.setattr("sys.argv", ["coreason-validate", "--schema=SystemNode", str(missing_file)])

    with pytest.raises(SystemExit) as exc_info:
        validate_main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "does not exist" in captured.err
