from pathlib import Path
from unittest.mock import patch

import pytest

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


def test_cli_visualize_missing_file(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("sys.argv", ["coreason-visualize", "ghost_file.json"]),
        patch("sys.exit", side_effect=SystemExit) as mock_exit,
    ):
        with pytest.raises(SystemExit):
            visualize_main()
        mock_exit.assert_called_once_with(1)
