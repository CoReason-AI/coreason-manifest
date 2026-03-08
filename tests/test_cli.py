import json
from pathlib import Path

import pytest

from coreason_manifest.cli.export import main as export_main
from coreason_manifest.cli.mcp_server import get_schema, list_schemas
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
