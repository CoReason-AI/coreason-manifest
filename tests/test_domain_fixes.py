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
from coreason_manifest.spec.interop.exceptions import SecurityJailViolationError
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
  version: "1.0.0"
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
  version: "1.0.0"
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
    with pytest.raises(SecurityJailViolationError, match="Dynamic code execution references detected"):
        load_flow_from_file(str(f))

    # 2. Allow: pass
    try:
        load_flow_from_file(str(f), allow_dynamic_execution=True)
    except SecurityJailViolationError:
        pytest.fail("SecurityJailViolationError raised despite allow_dynamic_execution=True")
    except Exception:
        # Pydantic might complain about other things, but security check passed
        pass


def test_dynamic_execution_check_list(tmp_path: Any) -> None:
    yaml_content = """
kind: LinearFlow
metadata:
  name: "DynamicList"
  version: "1.0.0"
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

    with pytest.raises(SecurityJailViolationError, match="Dynamic code execution references detected"):
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
  version: "1.0.0"
  description: "Desc"
  tags: []
sequence: []
definitions:
  skills:
    bad_path: "dir\\\\evil.py:Agent"
"""
    f = tmp_path / "win.yaml"
    f.write_text(yaml_content)

    # Should NOT raise SecurityJailViolationError because regex doesn't match
    load_flow_from_file(str(f))

    # POSIX path should be detected
    yaml_content_posix = """
kind: LinearFlow
metadata:
  name: "PosixPath"
  version: "1.0.0"
  description: "Desc"
  tags: []
sequence: []
definitions:
  skills:
    good_path: "dir/evil.py:Agent"
"""
    f2 = tmp_path / "posix.yaml"
    f2.write_text(yaml_content_posix)

    with pytest.raises(SecurityJailViolationError, match="Dynamic code execution references detected"):
        load_flow_from_file(str(f2))


def test_agent_loading_log(tmp_path: Any) -> None:
    py_file = tmp_path / "my_agent.py"
    py_file.write_text("class MyAgent: pass")
    py_file.chmod(0o600)

    # Verify warning
    with pytest.warns(RuntimeSecurityWarning, match="Dynamic Code Execution"):
        load_agent_from_ref(f"{py_file.name}:MyAgent", root_dir=tmp_path)


# Domain 3: Strict Schema Validation (Repair Removed)
def test_schema_strict_validation() -> None:
    """Ensure invalid schemas raise ValueError immediately."""
    from jsonschema.exceptions import SchemaError

    with patch("jsonschema.Draft7Validator.check_schema") as mock_check:
        mock_check.side_effect = SchemaError("Invalid schema")

        bad_schema: dict[str, Any] = {"type": "integer", "default": "bad"}

        with pytest.raises(ValueError, match="Invalid JSON Schema"):
            DataSchema(json_schema=bad_schema)


# Domain 4: Validator Coverage
def test_validator_coverage() -> None:
    # Helper to validate a node isolated in a graph with empty blackboard
    def check_node(node: Any, expected_error: str) -> None:
        graph = Graph(nodes={"n1": node}, edges=[], entry_point="n1")
        flow = GraphFlow(
            kind="GraphFlow",
            metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
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
