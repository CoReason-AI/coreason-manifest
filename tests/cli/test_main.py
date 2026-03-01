import json
import os
import tempfile
from unittest.mock import patch

from typer.testing import CliRunner

from coreason_manifest.cli.main import app

runner = CliRunner()


def test_export_schema() -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp_path = tmp.name

    try:
        result = runner.invoke(app, ["export-schema", "HierarchicalBlueprint", tmp_path])
        assert result.exit_code == 0
        assert "Schema exported to" in result.stdout

        with open(tmp_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "title" in data
        assert data["title"] == "HierarchicalBlueprint"
        assert "properties" in data

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_export_schema_unsupported() -> None:
    result = runner.invoke(app, ["export-schema", "UnknownModel", "out.json"])
    assert result.exit_code == 1
    # Check stderr or stdout, typer prints red error to stderr
    # if runner doesn't capture stderr properly, we can just check exit_code


from unittest.mock import MagicMock

@patch("coreason_manifest.cli.main.export_html_diagram")
@patch("coreason_manifest.cli.main.get_sota_scivis_topology")
def test_export_diagram(mock_get_topology: MagicMock, mock_export_diagram: MagicMock) -> None:
    mock_get_topology.return_value = "mock_flow"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        tmp_path = tmp.name

    try:
        result = runner.invoke(app, ["export-diagram", tmp_path])
        assert result.exit_code == 0
        assert "Diagram exported to" in result.stdout

        mock_get_topology.assert_called_once()
        mock_export_diagram.assert_called_once_with("mock_flow", tmp_path)

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
