from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
import yaml

from coreason_manifest.spec.core.flow import (
    Blackboard,
    DataSchema,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, InspectorNode, SwarmNode, SwitchNode
from coreason_manifest.utils.io import ManifestIO
from coreason_manifest.utils.loader import (
    RuntimeSecurityWarning,
    SecurityViolationError,
    construct_mapping_unique,
    load_agent_from_ref,
    load_flow_from_file,
)
from coreason_manifest.utils.validator import validate_flow


# Domain 1: Duplicate Keys
def test_duplicate_keys(tmp_path: Any) -> None:
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

    # PT011: Added match
    with pytest.raises(ValueError, match="found duplicate key"):
        load_flow_from_file(str(f))


def test_duplicate_keys_raises_error(tmp_path: Any) -> None:
    """Verifies that the UniqueKeyLoader actually prevents duplicate keys."""
    p = tmp_path / "dup_direct.yaml"
    # Create a YAML file with duplicate keys
    p.write_text("step1: {}\nstep1: {}", encoding="utf-8")
    with pytest.raises(ValueError, match="found duplicate key"):
        load_flow_from_file(str(p))


def test_construct_mapping_unique_validation() -> None:
    # Test that construct_mapping_unique raises ConstructorError if node is not a MappingNode
    # This covers lines 60-65 in loader.py
    loader = yaml.SafeLoader("")
    node = yaml.ScalarNode(tag="tag:yaml.org,2002:str", value="test")

    with pytest.raises(yaml.constructor.ConstructorError, match="expected a mapping node"):
        construct_mapping_unique(loader, node)


# Domain 2: Dynamic Execution
def test_dynamic_execution_check(tmp_path: Any) -> None:
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


def test_dynamic_execution_check_list(tmp_path: Any) -> None:
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


def test_dynamic_execution_posix_path_strictness(tmp_path: Any) -> None:
    """Test that dynamic ref regex enforces POSIX paths (no backslashes)."""
    # Windows path with backslash should NOT match the strict regex
    # Therefore, it is NOT flagged as a dynamic reference by the scanner.
    # This implies the system rejects non-POSIX paths for execution elsewhere.
    yaml_content = """
kind: LinearFlow
metadata:
  name: "WinPath"
  version: "1.0"
  description: "Desc"
  tags: []
sequence: []
definitions:
  skills:
    bad_path: "dir\\\\evil.py:Agent"
"""
    f = tmp_path / "win.yaml"
    f.write_text(yaml_content)

    # Should NOT raise SecurityViolationError because regex doesn't match
    load_flow_from_file(str(f))

    # POSIX path should be detected
    yaml_content_posix = """
kind: LinearFlow
metadata:
  name: "PosixPath"
  version: "1.0"
  description: "Desc"
  tags: []
sequence: []
definitions:
  skills:
    good_path: "dir/evil.py:Agent"
"""
    f2 = tmp_path / "posix.yaml"
    f2.write_text(yaml_content_posix)

    with pytest.raises(SecurityViolationError, match="Dynamic code execution references detected"):
        load_flow_from_file(str(f2))


def test_agent_loading_log(tmp_path: Any) -> None:
    py_file = tmp_path / "my_agent.py"
    py_file.write_text("class MyAgent: pass")

    # Verify warning
    with pytest.warns(RuntimeSecurityWarning, match="Dynamic Code Execution"):
        load_agent_from_ref(f"{py_file.name}:MyAgent", root_dir=tmp_path)


# Domain 3: Schema Repair
def test_schema_repair() -> None:
    with patch("jsonschema.Draft7Validator.check_schema") as mock_check:
        # Case 1: Missing Type
        # SOTA: Validation runs AFTER repair, so check_schema should succeed on the first call.
        mock_check.return_value = None
        bad_schema: dict[str, Any] = {"properties": {"foo": {}}}

        # PT031: Simplified warns block
        with pytest.warns(UserWarning, match="Schema repaired"):
            ds = DataSchema(json_schema=bad_schema)

        assert isinstance(ds.json_schema, dict)
        assert ds.json_schema["type"] == "object"

        # Case 2: Bad Default
        bad_schema_2: dict[str, Any] = {"type": "integer", "default": "bad"}

        ds = DataSchema(json_schema=bad_schema_2)
        assert isinstance(ds.json_schema, dict)
        assert "default" not in ds.json_schema


def test_schema_repair_extended() -> None:
    with patch("jsonschema.Draft7Validator.check_schema") as mock_check:
        # SOTA: Validation runs AFTER repair, so check_schema should succeed on the first call.
        mock_check.return_value = None

        # String mismatch: "123" (int) -> "123"
        bad_str: dict[str, Any] = {"type": "string", "default": 123}
        ds = DataSchema(json_schema=bad_str)
        assert isinstance(ds.json_schema, dict)
        assert ds.json_schema["default"] == "123"

        # Boolean mismatch: "true" -> True
        bad_bool: dict[str, Any] = {"type": "boolean", "default": "true"}
        ds = DataSchema(json_schema=bad_bool)
        assert isinstance(ds.json_schema, dict)
        assert ds.json_schema["default"] is True

        # Boolean mismatch: "false" -> False
        bad_bool_f: dict[str, Any] = {"type": "boolean", "default": "FALSE"}
        ds = DataSchema(json_schema=bad_bool_f)
        assert isinstance(ds.json_schema, dict)
        assert ds.json_schema["default"] is False

        # Boolean fail
        bad_bool_x: dict[str, Any] = {"type": "boolean", "default": "notbool"}
        ds = DataSchema(json_schema=bad_bool_x)
        assert isinstance(ds.json_schema, dict)
        assert "default" not in ds.json_schema

        # Integer mismatch: "123" -> 123
        bad_int: dict[str, Any] = {"type": "integer", "default": "123"}
        ds = DataSchema(json_schema=bad_int)
        assert isinstance(ds.json_schema, dict)
        assert ds.json_schema["default"] == 123

        # Integer fail
        bad_int_x: dict[str, Any] = {"type": "integer", "default": "abc"}
        ds = DataSchema(json_schema=bad_int_x)
        assert isinstance(ds.json_schema, dict)
        assert "default" not in ds.json_schema

        # Integer bool conflict (bool is int subclass but should not auto-cast)
        bad_int_bool: dict[str, Any] = {"type": "integer", "default": True}
        ds = DataSchema(json_schema=bad_int_bool)
        assert isinstance(ds.json_schema, dict)
        assert "default" not in ds.json_schema

        # Float mismatch: "12.5" -> 12.5
        bad_float: dict[str, Any] = {"type": "float", "default": "12.5"}
        ds = DataSchema(json_schema=bad_float)
        assert isinstance(ds.json_schema, dict)
        assert ds.json_schema["default"] == 12.5

        # Float fail
        bad_float_x: dict[str, Any] = {"type": "float", "default": "abc"}
        ds = DataSchema(json_schema=bad_float_x)
        assert isinstance(ds.json_schema, dict)
        assert "default" not in ds.json_schema

        # Object mismatch
        bad_obj: dict[str, Any] = {"type": "object", "default": []}
        ds = DataSchema(json_schema=bad_obj)
        assert isinstance(ds.json_schema, dict)
        assert "default" not in ds.json_schema

        # Array mismatch
        bad_arr: dict[str, Any] = {"type": "array", "default": {}}
        ds = DataSchema(json_schema=bad_arr)
        assert isinstance(ds.json_schema, dict)
        assert "default" not in ds.json_schema


def test_recursive_schema_repair() -> None:
    """Verify that schema repair traverses nested properties and arrays."""
    with patch("jsonschema.Draft7Validator.check_schema") as mock_check:
        # SOTA: Validation runs AFTER repair, so check_schema should succeed on the first call.
        mock_check.return_value = None

        # Nested structure:
        # properties -> user -> default "bad_int" for integer
        # items -> default "bad_bool" for boolean
        nested_schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "integer",
                    "default": "bad_int",  # Should be removed
                },
                "meta": {
                    "type": "array",
                    "items": {
                        "type": "boolean",
                        "default": "not_bool",  # Should be removed
                    },
                },
            },
        }

        with pytest.warns(UserWarning, match="Schema repaired"):
            ds = DataSchema(json_schema=nested_schema)

        # Assertions
        assert isinstance(ds.json_schema, dict)
        user_schema = ds.json_schema["properties"]["user"]
        assert "default" not in user_schema

        items_schema = ds.json_schema["properties"]["meta"]["items"]
        assert "default" not in items_schema


def test_recursive_schema_repair_definitions() -> None:
    """Verify that schema repair traverses definitions/$defs."""
    with patch("jsonschema.Draft7Validator.check_schema") as mock_check:
        # SOTA: Validation runs AFTER repair, so check_schema should succeed on the first call.
        mock_check.return_value = None

        defs_schema: dict[str, Any] = {
            "definitions": {
                "shared": {
                    "type": "integer",
                    "default": "bad_shared",
                }
            },
            "$defs": {
                "other": {
                    "type": "boolean",
                    "default": "bad_bool",
                }
            },
        }

        with pytest.warns(UserWarning, match="Schema repaired"):
            ds = DataSchema(json_schema=defs_schema)

        assert isinstance(ds.json_schema, dict)
        shared = ds.json_schema["definitions"]["shared"]
        assert "default" not in shared

        other = ds.json_schema["$defs"]["other"]
        assert "default" not in other


# Domain 4: Validator Coverage
def test_validator_coverage() -> None:
    # Helper to validate a node isolated in a graph with empty blackboard
    def check_node(node: Any, expected_error: str) -> None:
        graph = Graph(nodes={"n1": node}, edges=[])
        flow = GraphFlow(
            kind="GraphFlow",
            metadata=FlowMetadata(name="T", version="1", description="D", tags=[]),
            interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
            blackboard=Blackboard(variables={}, persistence=False),
            graph=graph,
        )
        errors = validate_flow(flow)
        assert any(expected_error in e for e in errors), f"Expected '{expected_error}' in {errors}"

    # SwarmNode missing vars
    swarm = SwarmNode(
        id="n1",
        type="swarm",
        metadata={},
        resilience=None,
        worker_profile="p1",
        workload_variable="missing_work",
        distribution_strategy="sharded",
        max_concurrency=1,
        reducer_function="concat",
        output_variable="missing_out",
    )
    check_node(swarm, "SwarmNode 'n1' references missing variable 'missing_work'")
    check_node(swarm, "SwarmNode 'n1' writes to missing variable 'missing_out'")

    # SwitchNode missing variable (already covered by existing test, but ensuring line hit)
    switch = SwitchNode(id="n1", type="switch", metadata={}, variable="missing_switch", cases={}, default="n1")
    check_node(switch, "SwitchNode 'n1' evaluates missing variable 'missing_switch'")

    # InspectorNode missing vars
    insp = InspectorNode(
        id="n1",
        type="inspector",
        metadata={},
        resilience=None,
        target_variable="missing_target",
        criteria="c",
        pass_threshold=0.5,
        output_variable="missing_out",
    )
    check_node(insp, "InspectorNode 'n1' inspects missing variable 'missing_target'")
    check_node(insp, "InspectorNode 'n1' writes to missing variable 'missing_out'")

    # AgentNode missing vars
    agent = AgentNode(
        id="n1",
        type="agent",
        metadata={"desc": "Using {{ missing_meta }}"},
        resilience=None,
        profile=CognitiveProfile(
            role="Role with {{ missing_role }}",
            persona="Persona with {{ missing_persona }}",
            reasoning=None,
            fast_path=None,
        ),
        tools=[],
    )
    check_node(agent, "AgentNode 'n1' references missing variable 'missing_meta'")
    check_node(agent, "AgentNode 'n1' references missing variable 'missing_role'")
    check_node(agent, "AgentNode 'n1' references missing variable 'missing_persona'")


def test_manifest_io_coverage(tmp_path: Any) -> None:
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


def test_manifest_io_symlink_loop_coverage(tmp_path: Any) -> None:
    loader = ManifestIO(root_dir=tmp_path)

    # Mock pathlib.Path.resolve to raise RuntimeError("Symlink loop")
    # This covers lines 60-62 in io.py
    with (
        patch("pathlib.Path.resolve", side_effect=RuntimeError("Symlink loop")),
        pytest.raises(SecurityViolationError, match="Symlink detected during path resolution"),
    ):
        loader.read_text("some_file")


def test_manifest_io_posix_permissions(tmp_path: Any) -> None:
    import stat

    loader = ManifestIO(root_dir=tmp_path)
    f = tmp_path / "world_writable.yaml"
    f.write_text("content")

    # Simulate world-writable permissions
    mock_stat = MagicMock()
    mock_stat.st_mode = stat.S_IWOTH

    # Mock _is_posix property and os.fstat
    with (
        patch("coreason_manifest.utils.io.ManifestIO._is_posix", new_callable=PropertyMock) as mock_posix,
        patch("os.fstat", return_value=mock_stat),
    ):
        mock_posix.return_value = True
        with pytest.raises(SecurityViolationError, match="Unsafe Permissions"):
            loader.read_text("world_writable.yaml")


def test_manifest_io_fdopen_error(tmp_path: Any) -> None:
    loader = ManifestIO(root_dir=tmp_path)
    f = tmp_path / "test.yaml"
    f.write_text("content")

    # Mock _read_from_fd to raise an error
    # We also mock os.close to verify it's called
    with (
        patch.object(ManifestIO, "_read_from_fd", side_effect=OSError("read failed")),
        patch("os.close") as mock_close,
    ):
        with pytest.raises(OSError, match="read failed"):
            loader.read_text("test.yaml")

        # Verify os.close was called (cleanup logic)
        mock_close.assert_called()
