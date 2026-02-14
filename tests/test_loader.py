from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pytest
import yaml

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.utils.loader import load_flow_from_file


def test_load_linear_flow() -> None:
    data: dict[str, Any] = {
        "kind": "LinearFlow",
        "metadata": {"name": "TestLinear", "version": "1.0", "description": "Test", "tags": []},
        "sequence": [],
    }
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(data, tmp)
        tmp_path = tmp.name

    try:
        flow = load_flow_from_file(tmp_path)
        assert isinstance(flow, LinearFlow)
        assert flow.metadata.name == "TestLinear"
    finally:
        Path(tmp_path).unlink()


def test_load_graph_flow() -> None:
    data: dict[str, Any] = {
        "kind": "GraphFlow",
        "metadata": {"name": "TestGraph", "version": "1.0", "description": "Test", "tags": []},
        "interface": {
            "inputs": {"fields": {}, "required": []},
            "outputs": {"fields": {}, "required": []},
        },
        "blackboard": None,
        "graph": {"nodes": {}, "edges": []},
    }
    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        # JSON is also valid YAML
        import json

        json.dump(data, tmp)
        tmp_path = tmp.name

    try:
        flow = load_flow_from_file(tmp_path)
        assert isinstance(flow, GraphFlow)
        assert flow.metadata.name == "TestGraph"
    finally:
        Path(tmp_path).unlink()


def test_load_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_flow_from_file("non_existent_file.yaml")


def test_load_invalid_yaml() -> None:
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp.write("invalid: yaml: [")
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="Failed to parse manifest file"):
            load_flow_from_file(tmp_path)
    finally:
        Path(tmp_path).unlink()


def test_load_not_a_dict() -> None:
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp.write("- list item\n- list item 2")
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="Manifest content must be a dictionary"):
            load_flow_from_file(tmp_path)
    finally:
        Path(tmp_path).unlink()


def test_load_unknown_kind() -> None:
    data: dict[str, Any] = {"kind": "UnknownKind"}
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(data, tmp)
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="Unknown or missing manifest kind"):
            load_flow_from_file(tmp_path)
    finally:
        Path(tmp_path).unlink()
