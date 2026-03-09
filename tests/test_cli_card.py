# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from coreason_manifest.cli.card import main as card_main


def test_card_valid_envelope(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload_path = tmp_path / "valid_envelope.json"
    envelope_data = {
        "manifest_version": "1.0.0",
        "topology": {
            "type": "dag",
            "max_depth": 10,
            "max_fan_out": 10,
            "lifecycle_phase": "live",
            "architectural_intent": "Linear extraction sequence",
            "justification": "Ensures deterministic token bounds.",
            "nodes": {
                "did:web:agent-1": {
                    "type": "agent",
                    "description": "Extractor",
                    "architectural_intent": "Parse PDF",
                    "justification": "Required for preprocessing.",
                    "agent_attestation": {
                        "training_lineage_hash": "a" * 64,
                        "developer_signature": "sig",
                        "capability_merkle_root": "b" * 64,
                    },
                }
            },
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
    assert "Linear extraction sequence" in captured.out
    assert "did:web:agent-1" in captured.out
    assert "Parse PDF" in captured.out


def test_card_invalid_envelope(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload_path = tmp_path / "invalid_envelope.json"
    payload_path.write_text('{"invalid": "data"}')

    with (
        patch("sys.argv", ["coreason-card", str(payload_path)]),
        patch("sys.exit", side_effect=SystemExit) as mock_exit,
    ):
        with pytest.raises(SystemExit):
            card_main()
        mock_exit.assert_called_once_with(1)

    captured = capsys.readouterr()
    assert "Envelope Validation Error" in captured.err


def test_card_missing_file(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("sys.argv", ["coreason-card", "ghost_file.json"]),
        patch("sys.exit", side_effect=SystemExit) as mock_exit,
    ):
        with pytest.raises(SystemExit):
            card_main()
        mock_exit.assert_called_once_with(1)

    captured = capsys.readouterr()
    assert "not found" in captured.err
