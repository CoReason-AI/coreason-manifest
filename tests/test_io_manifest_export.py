import contextlib
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

# Import the code to test
# Assuming src is in python path or installed
try:
    from coreason_manifest.utils.io import export_manifest
except ImportError:
    import sys

    sys.path.append(str(Path(__file__).parents[2] / "src"))
    from coreason_manifest.utils.io import export_manifest


class MockPydanticModel:
    def __init__(self, data: dict[str, Any]):
        self.data = data

    def model_dump(self, exclude_none: bool = False, by_alias: bool = False) -> dict[str, Any]:
        # Mimic Pydantic behavior:
        # exclude_none: remove keys with None values
        # by_alias: we'll just ignore it for this mock as we don't define aliases
        _ = by_alias  # Silence unused argument warning

        result = {}
        for k, v in self.data.items():
            if exclude_none and v is None:
                continue
            result[k] = v
        return result


def test_export_manifest_sorting() -> None:
    # Define data with mixed priority, depriority, and normal keys
    # Intentionally unordered in the input dict
    data = {
        "nodes": ["node1", "node2"],  # Depriority (index 4 in list)
        "zebra": "stripe",  # Normal (z)
        "apiVersion": "v1",  # Priority (index 0)
        "apple": "fruit",  # Normal (a)
        "kind": "Agent",  # Priority (index 2)
        "definitions": {"foo": "bar"},  # Depriority (index 0)
        "name": "MyAgent",  # Priority (index 4)
        "type": "standard",  # Priority (index 1)
        "ignored": None,  # Should be excluded
        "graph": "graph_data",  # Depriority (index 3)
    }

    model = MockPydanticModel(data)

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        # Close the file so export_manifest can write to it (windows compatibility mostly, but good practice)
        tmp.close()

        export_manifest(model, tmp_path)

        with open(tmp_path, encoding="utf-8") as f:
            content = f.read()
            loaded = yaml.safe_load(content)

        # Verify keys exist and None is excluded
        assert "ignored" not in loaded
        assert loaded["apiVersion"] == "v1"

        keys_in_order = list(loaded.keys())

        # Expected Order:
        # Priority Keys (0):
        # 1. apiVersion (index 0)
        # 2. type (index 1)
        # 3. kind (index 2)
        # 4. name (index 4)

        # Normal Keys (1):
        # 5. apple (a)
        # 6. zebra (z)

        # Depriority Keys (2):
        # 7. definitions (index 0)
        # 8. graph (index 3)
        # 9. nodes (index 4)

        expected_order = [
            "apiVersion",
            "type",
            "kind",
            "name",
            "apple",
            "zebra",
            "definitions",
            "graph",
            "nodes",
        ]

        assert keys_in_order == expected_order

    finally:
        if tmp_path.exists():
            with contextlib.suppress(OSError):
                os.remove(tmp_path)


def test_export_manifest_nested_sorting() -> None:
    # Test recursive sorting
    data = {
        "metadata": {"version": "1.0", "name": "meta", "id": "123"},
        "apiVersion": "v1",
    }
    # "metadata" is priority.
    # Inside "metadata":
    # "id" (priority), "name" (priority), "version" (normal)

    model = MockPydanticModel(data)

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        tmp.close()
        export_manifest(model, tmp_path)

        with open(tmp_path, encoding="utf-8") as f:
            content = f.read()
            loaded = yaml.safe_load(content)

        keys_in_order = list(loaded.keys())
        assert keys_in_order == ["apiVersion", "metadata"]

        metadata_keys = list(loaded["metadata"].keys())
        # Inside metadata: "id", "name" are priority keys. "version" is normal.
        # "id" is index 3 in priority list.
        # "name" is index 4 in priority list.
        # So "id" comes before "name".
        assert metadata_keys == ["id", "name", "version"]

    finally:
        if tmp_path.exists():
            with contextlib.suppress(OSError):
                os.remove(tmp_path)


def test_export_manifest_mixed_types() -> None:
    # Test with non-string keys if possible (though JSON/YAML usually have string keys for mappings)
    # But ManifestDumper logic casts to string.
    # Let's test just string keys but that resemble numbers?

    data = {"10": "ten", "2": "two", "kind": "test"}
    # "kind" is priority.
    # "10", "2" are normal.
    # Alphabetical: "10" < "2".

    model = MockPydanticModel(data)
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        tmp.close()
        export_manifest(model, tmp_path)
        with open(tmp_path, encoding="utf-8") as f:
            loaded = yaml.safe_load(f)

        keys = list(loaded.keys())
        assert keys == ["kind", "10", "2"]

    finally:
        if tmp_path.exists():
            with contextlib.suppress(OSError):
                os.remove(tmp_path)
