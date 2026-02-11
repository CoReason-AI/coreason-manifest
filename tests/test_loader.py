from pathlib import Path
from tempfile import NamedTemporaryFile
import yaml
import pytest

from coreason_manifest.utils.loader import load_flow_from_file
from coreason_manifest.spec.core.flow import LinearFlow, GraphFlow

def test_load_linear_flow():
    data = {
        "kind": "LinearFlow",
        "metadata": {
            "name": "TestLinear",
            "version": "1.0",
            "description": "Test",
            "tags": []
        },
        "sequence": [],
        "tool_packs": []
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

def test_load_graph_flow():
    data = {
        "kind": "GraphFlow",
        "metadata": {
            "name": "TestGraph",
            "version": "1.0",
            "description": "Test",
            "tags": []
        },
        "interface": {"inputs": {}, "outputs": {}},
        "blackboard": None,
        "graph": {"nodes": {}, "edges": []},
        "tool_packs": []
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

def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_flow_from_file("non_existent_file.yaml")

def test_load_invalid_yaml():
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp.write("invalid: yaml: [")
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="Failed to parse manifest file"):
            load_flow_from_file(tmp_path)
    finally:
        Path(tmp_path).unlink()

def test_load_not_a_dict():
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp.write("- list item\n- list item 2")
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="Manifest content must be a dictionary"):
            load_flow_from_file(tmp_path)
    finally:
        Path(tmp_path).unlink()

def test_load_unknown_kind():
    data = {"kind": "UnknownKind"}
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(data, tmp)
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="Unknown or missing manifest kind"):
            load_flow_from_file(tmp_path)
    finally:
        Path(tmp_path).unlink()
