# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from pathlib import Path
from unittest.mock import patch

from coreason_manifest.cli.validate import main


def test_cli_validate_success(tmp_path: Path) -> None:
    payload = tmp_path / "payload.json"
    payload.write_text('{"op": "add", "path": "/foo", "value": "bar"}')
    with patch("sys.argv", ["validate", "--step", "state_differential", str(payload)]), patch("sys.exit") as mock_exit:
        main()
        mock_exit.assert_called_with(0)


def test_cli_validate_missing_file() -> None:
    with (
        patch("sys.argv", ["validate", "--step", "state_differential", "missing.json"]),
        patch("sys.exit") as mock_exit,
        patch("sys.stderr.write"),
    ):
        main()
        mock_exit.assert_called_with(1)


def test_cli_validate_invalid_schema(tmp_path: Path) -> None:
    payload = tmp_path / "payload.json"
    payload.write_text('{"invalid": "data"}')
    with (
        patch("sys.argv", ["validate", "--step", "state_differential", str(payload)]),
        patch("sys.exit") as mock_exit,
        patch("sys.stderr.write"),
    ):
        main()
        mock_exit.assert_called_with(1)


def test_cli_validate_invalid_step(tmp_path: Path) -> None:
    payload = tmp_path / "payload.json"
    payload.write_text("{}")
    with (
        patch("sys.argv", ["validate", "--step", "unknown", str(payload)]),
        patch("sys.exit") as mock_exit,
        patch("sys.stderr.write"),
    ):
        main()
        mock_exit.assert_called_with(1)
