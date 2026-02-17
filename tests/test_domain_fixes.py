import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from jsonschema.exceptions import SchemaError
import warnings

from coreason_manifest.utils.loader import (
    load_flow_from_file,
    load_agent_from_ref,
    SecurityViolationError,
    RuntimeSecurityWarning,
    UniqueKeyLoader
)
from coreason_manifest.spec.core.flow import DataSchema, GraphFlow, Graph, Blackboard, VariableDef, FlowMetadata, FlowInterface
from coreason_manifest.spec.core.nodes import SwarmNode, SwitchNode, InspectorNode
from coreason_manifest.utils.validator import validate_flow
from coreason_manifest.utils.logger import logger
from coreason_manifest.utils.io import ManifestIO

# Domain 1: Duplicate Keys
def test_duplicate_keys(tmp_path):
    yaml_content = """
kind: LinearFlow
metadata:
  name: "Dup"
  version: "1.0"
  description: "Desc"
  tags: []
sequence: []
metadata:
  name: "Dup2"
"""
    f = tmp_path / "dup.yaml"
    f.write_text(yaml_content)

    with pytest.raises(ValueError) as excinfo:
        load_flow_from_file(str(f))

    # load_flow_from_file wraps yaml errors in ValueError
    assert "found duplicate key" in str(excinfo.value)

# Domain 2: Dynamic Execution
def test_dynamic_execution_check(tmp_path):
    # Use a valid yaml structure but with dynamic ref string
    yaml_content = """
kind: LinearFlow
metadata:
  name: "Dynamic"
  version: "1.0"
  description: "Desc"
  tags: ["test"]
sequence: []
# Hidden dynamic ref in definitions (arbitrary dict)
definitions:
  skills:
    my_skill: "evil.py:Agent"
"""
    f = tmp_path / "dynamic.yaml"
    f.write_text(yaml_content)

    # 1. Default: fail
    with pytest.raises(SecurityViolationError, match="Dynamic code execution references detected"):
        load_flow_from_file(str(f))

    # 2. Allow: pass
    try:
        load_flow_from_file(str(f), allow_dynamic_execution=True)
    except SecurityViolationError:
        pytest.fail("SecurityViolationError raised despite allow_dynamic_execution=True")
    except Exception:
        # Pydantic might complain about other things, but security check passed
        pass

def test_dynamic_execution_check_list(tmp_path):
    yaml_content = """
kind: LinearFlow
metadata:
  name: "DynamicList"
  version: "1.0"
  description: "Desc"
  tags: []
sequence: []
# Hidden dynamic ref in list
definitions:
  skills:
    my_list: ["safe", "evil.py:Agent"]
"""
    f = tmp_path / "dynamic_list.yaml"
    f.write_text(yaml_content)

    with pytest.raises(SecurityViolationError, match="Dynamic code execution references detected"):
        load_flow_from_file(str(f))

def test_agent_loading_log(tmp_path):
    py_file = tmp_path / "my_agent.py"
    py_file.write_text("class MyAgent: pass")

    # Verify warning
    with pytest.warns(RuntimeSecurityWarning, match="Dynamic Code Execution"):
        load_agent_from_ref(f"{py_file.name}:MyAgent", root_dir=tmp_path)

# Domain 3: Schema Repair
def test_schema_repair():
    with patch("jsonschema.Draft7Validator.check_schema") as mock_check:
        # Case 1: Missing Type
        mock_check.side_effect = [SchemaError("Simulated"), None]
        bad_schema = {"properties": {"foo": {}}}

        with pytest.warns(UserWarning, match="Schema repaired"):
            ds = DataSchema(json_schema=bad_schema)
            assert ds.json_schema["type"] == "object"

        # Case 2: Bad Default
        mock_check.side_effect = [SchemaError("Simulated"), None]
        bad_schema_2 = {"type": "integer", "default": "bad"}

        ds = DataSchema(json_schema=bad_schema_2)
        assert "default" not in ds.json_schema

def test_schema_repair_extended():
    with patch("jsonschema.Draft7Validator.check_schema") as mock_check:
        # String mismatch
        mock_check.side_effect = [SchemaError("Simulated"), None]
        bad_str = {"type": "string", "default": 123}
        ds = DataSchema(json_schema=bad_str)
        assert "default" not in ds.json_schema

        # Boolean mismatch
        mock_check.side_effect = [SchemaError("Simulated"), None]
        bad_bool = {"type": "boolean", "default": "true"} # string "true" is not bool
        ds = DataSchema(json_schema=bad_bool)
        assert "default" not in ds.json_schema

        # Object mismatch
        mock_check.side_effect = [SchemaError("Simulated"), None]
        bad_obj = {"type": "object", "default": []}
        ds = DataSchema(json_schema=bad_obj)
        assert "default" not in ds.json_schema

        # Array mismatch
        mock_check.side_effect = [SchemaError("Simulated"), None]
        bad_arr = {"type": "array", "default": {}}
        ds = DataSchema(json_schema=bad_arr)
        assert "default" not in ds.json_schema

# Domain 4: Validator Coverage
def test_validator_coverage():
    # Helper to validate a node isolated in a graph with empty blackboard
    def check_node(node, expected_error):
        graph = Graph(nodes={"n1": node}, edges=[])
        flow = GraphFlow(
            kind="GraphFlow",
            metadata=FlowMetadata(name="T", version="1", description="D", tags=[]),
            interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
            blackboard=Blackboard(variables={}, persistence=False),
            graph=graph
        )
        errors = validate_flow(flow)
        assert any(expected_error in e for e in errors), f"Expected '{expected_error}' in {errors}"

    # SwarmNode missing vars
    swarm = SwarmNode(
        id="n1", type="swarm", metadata={}, resilience=None,
        worker_profile="p1", workload_variable="missing_work",
        distribution_strategy="sharded", max_concurrency=1,
        reducer_function="concat", output_variable="missing_out"
    )
    check_node(swarm, "SwarmNode 'n1' references missing variable 'missing_work'")
    check_node(swarm, "SwarmNode 'n1' writes to missing variable 'missing_out'")

    # SwitchNode missing variable (already covered by existing test, but ensuring line hit)
    switch = SwitchNode(
        id="n1", type="switch", metadata={}, variable="missing_switch",
        cases={}, default="n1"
    )
    check_node(switch, "SwitchNode 'n1' evaluates missing variable 'missing_switch'")

    # InspectorNode missing vars
    insp = InspectorNode(
        id="n1", type="inspector", metadata={}, resilience=None,
        target_variable="missing_target", criteria="c", pass_threshold=0.5,
        output_variable="missing_out"
    )
    check_node(insp, "InspectorNode 'n1' inspects missing variable 'missing_target'")
    check_node(insp, "InspectorNode 'n1' writes to missing variable 'missing_out'")

def test_manifest_io_coverage(tmp_path):
    loader = ManifestIO(root_dir=tmp_path)

    # Not a dict
    f1 = tmp_path / "list.yaml"
    f1.write_text("- item1\n- item2")
    with pytest.raises(ValueError, match="Manifest content must be a dictionary"):
        loader.load("list.yaml")

    # Invalid YAML
    f2 = tmp_path / "invalid.yaml"
    f2.write_text("key: value: invalid")
    with pytest.raises(ValueError, match="Failed to parse manifest file"):
        loader.load("invalid.yaml")
