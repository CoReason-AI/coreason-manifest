from pathlib import Path
from typing import Any

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


def test_export_main_import_error(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import importlib

    original_import_module = importlib.import_module

    def mock_import_module(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "coreason_manifest":
            raise ImportError("Simulated ImportError")
        return original_import_module(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", mock_import_module)
    with pytest.raises(SystemExit) as exc_info:
        export_main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Failed to import coreason_manifest" in captured.out


def test_export_main_domain_import_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    import importlib

    original_import_module = importlib.import_module

    def mock_import_module(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "coreason_manifest.core":
            raise ImportError("Simulated domain ImportError")
        return original_import_module(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", mock_import_module)
    export_main()
    assert (tmp_path / "coreason_ontology.schema.json").exists()


def test_export_main_no_models(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import importlib

    original_import_module = importlib.import_module

    def mock_import_module(name: str, *args: Any, **kwargs: Any) -> Any:
        mod = original_import_module(name, *args, **kwargs)
        if name.startswith("coreason_manifest") and hasattr(mod, "__all__"):
            monkeypatch.setattr(mod, "__all__", [])
        return mod

    monkeypatch.setattr(importlib, "import_module", mock_import_module)

    with pytest.raises(SystemExit) as exc_info:
        export_main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "No models found to export." in captured.out


def test_mcp_server_schemas_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    original_import_module = importlib.import_module

    def mock_import_module(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "coreason_manifest.core":
            raise ImportError("Simulated domain ImportError for mcp_server")
        return original_import_module(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", mock_import_module)
    schemas = list_schemas()
    assert len(schemas) > 0


def test_mcp_server_get_schema_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    original_import_module = importlib.import_module

    def mock_import_module(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "coreason_manifest.core":
            raise ImportError("Simulated domain ImportError for mcp_server")
        return original_import_module(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", mock_import_module)

    # We still have schema in `coreason_manifest.core` fallback?
    # Actually, we just need to ensure the ImportError is caught.
    # We can try to get a schema that is not in `coreason_manifest.core` but exists.
    schema = get_schema("WorkflowEnvelope")
    assert schema["title"] == "WorkflowEnvelope"
