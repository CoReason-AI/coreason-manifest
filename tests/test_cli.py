import json
from pathlib import Path
from unittest.mock import patch

import pytest

from coreason_manifest.cli.export import main as export_main
from coreason_manifest.cli.visualize import main as visualize_main


def test_export_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    export_main()
    assert (tmp_path / "coreason_ontology.schema.json").exists()


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


@pytest.mark.anyio
async def test_mcp_server_rbac_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    from coreason_manifest.cli.mcp_server import _AVAILABLE_SCHEMAS, mcp

    # Inject a mock proprietary schema
    proprietary_name = "MockProprietarySchema"
    _AVAILABLE_SCHEMAS[proprietary_name] = {"title": "MockProprietarySchema", "x-required-licenses": ["marketscan"]}
    # We must append to _SCHEMA_NAMES to make it visible
    from coreason_manifest.cli.mcp_server import _SCHEMA_NAMES

    _SCHEMA_NAMES.append(proprietary_name)

    try:
        # TEST 1: Zero-Trust Default (No license)
        monkeypatch.delenv("COREASON_GRANTED_LICENSES", raising=False)

        with pytest.raises(Exception, match="not found"):
            await mcp.read_resource(f"schema://epistemic/{proprietary_name}")

        # TEST 2: Granted Context (Subset satisfied)
        monkeypatch.setenv("COREASON_GRANTED_LICENSES", "rightfind, marketscan ")

        res = await mcp.read_resource(f"schema://epistemic/{proprietary_name}")

        if isinstance(res, list) and len(res) > 0 and hasattr(res[0], 'content'):
            res = res[0].content
        if isinstance(res, bytes):
            res = res.decode("utf-8")

        schema = json.loads(str(res))
        assert schema["title"] == "MockProprietarySchema"

    finally:
        # Clean up
        _AVAILABLE_SCHEMAS.pop(proprietary_name, None)
        if proprietary_name in _SCHEMA_NAMES:
            _SCHEMA_NAMES.remove(proprietary_name)
