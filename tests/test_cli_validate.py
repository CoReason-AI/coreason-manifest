from unittest.mock import patch

from coreason_manifest.cli.validate import main


def test_cli_validate_success(tmp_path):
    payload = tmp_path / "payload.json"
    payload.write_text('{"op": "add", "path": "/foo", "value": "bar"}')
    with patch("sys.argv", ["validate", "--step", "delta_update", str(payload)]), patch("sys.exit") as mock_exit:
        main()
        mock_exit.assert_called_with(0)


def test_cli_validate_missing_file():
    with (
        patch("sys.argv", ["validate", "--step", "delta_update", "missing.json"]),
        patch("sys.exit") as mock_exit,
        patch("sys.stderr.write"),
    ):
        main()
        mock_exit.assert_called_with(1)


def test_cli_validate_invalid_schema(tmp_path):
    payload = tmp_path / "payload.json"
    payload.write_text('{"invalid": "data"}')
    with (
        patch("sys.argv", ["validate", "--step", "delta_update", str(payload)]),
        patch("sys.exit") as mock_exit,
        patch("sys.stderr.write"),
    ):
        main()
        mock_exit.assert_called_with(1)


def test_cli_validate_invalid_step(tmp_path):
    payload = tmp_path / "payload.json"
    payload.write_text("{}")
    with (
        patch("sys.argv", ["validate", "--step", "unknown", str(payload)]),
        patch("sys.exit") as mock_exit,
        patch("sys.stderr.write"),
    ):
        main()
        mock_exit.assert_called_with(1)
