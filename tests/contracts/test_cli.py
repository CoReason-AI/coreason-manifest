import json
from pathlib import Path
from unittest.mock import patch

import pytest

from coreason_manifest.cli.card import main as card_main
from coreason_manifest.cli.export import main as export_main
from coreason_manifest.cli.validate import main as validate_main
from coreason_manifest.cli.visualize import main as visualize_main


def test_cli_export_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    export_main()
    assert (tmp_path / "coreason_ontology.schema.json").exists()


def test_cli_validate_success(tmp_path: Path) -> None:
    payload = tmp_path / "payload.json"
    payload.write_text('{"op": "add", "path": "/foo", "value": "bar"}')
    with patch("sys.argv", ["validate", "--step", "state_differential", str(payload)]), patch("sys.exit") as mock_exit:
        validate_main()
        mock_exit.assert_called_with(0)


def test_cli_visualize_missing_file() -> None:
    with (
        patch("sys.argv", ["coreason-visualize", "ghost_file.json"]),
        patch("sys.exit", side_effect=SystemExit) as mock_exit,
    ):
        with pytest.raises(SystemExit):
            visualize_main()
        mock_exit.assert_called_once_with(1)


def test_cli_visualize_valid(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload_path = tmp_path / "valid_manifest.json"
    manifest_data = {
        "manifest_id": "manifest-test-01",
        "artifact_profile": {
            "artifact_event_id": "root-artifact",
            "detected_modalities": ["text"],
            "token_density": 100,
        },
        "active_subgraphs": {"text": ["did:web:agent-1"]},
        "bypassed_steps": [],
        "branch_budgets_magnitude": {"did:web:agent-1": 1000},
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


def test_cli_card_valid(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload_path = tmp_path / "valid_envelope.json"
    envelope_data = {
        "manifest_version": "1.0.0",
        "topology": {
            "type": "dag",
            "max_depth": 10,
            "max_fan_out": 10,
            "lifecycle_phase": "live",
            "nodes": {"did:web:agent-1": {"type": "system", "description": "Extractor"}},
            "edges": [],
            "allow_cycles": False,
        },
    }
    payload_path.write_text(json.dumps(envelope_data))

    with (
        patch("sys.argv", ["coreason-card", str(payload_path)]),
        patch("sys.exit", side_effect=SystemExit) as mock_exit,
    ):
        with pytest.raises(SystemExit):
            card_main()
        mock_exit.assert_called_once_with(0)

    captured = capsys.readouterr()
    assert "# CoReason Agent Card" in captured.out
    assert "did:web:agent-1" in captured.out
