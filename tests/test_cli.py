from pathlib import Path

import pytest

from coreason_manifest.cli.export import main as export_main
from coreason_manifest.cli.mcp_server import get_schema, list_schemas


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
