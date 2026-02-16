import os
import sys
import time
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from coreason_manifest.spec.core.flow import FlowDefinitions, FlowMetadata, LinearFlow
from coreason_manifest.spec.core.governance import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    Governance,
    check_circuit,
)
from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.utils.gatekeeper import validate_policy
from coreason_manifest.utils.loader import SecurityViolationError, load_agent_from_ref


# Test 1: Malicious Agent (AST check)
def test_malicious_agent_ast(tmp_path: Path) -> None:
    # 1. Test direct import
    agent_code = "import os"
    agent_file = tmp_path / "malicious.py"
    agent_file.write_text(agent_code)

    with pytest.raises(SecurityViolationError, match="Banned import 'os'"):
        load_agent_from_ref("malicious.py:MaliciousAgent", root_dir=tmp_path)

    # 2. Test from import
    agent_code_from = "from subprocess import run"
    agent_file_from = tmp_path / "malicious_from.py"
    agent_file_from.write_text(agent_code_from)

    with pytest.raises(SecurityViolationError, match="Banned import 'subprocess'"):
        load_agent_from_ref("malicious_from.py:MaliciousAgent", root_dir=tmp_path)


# Test 2: Permissions Test
def test_permissions_check(tmp_path: Path) -> None:
    if os.name != "posix":
        pytest.skip("Skipping permissions test on non-POSIX system")

    agent_code = """
class SafeAgent:
    pass
"""
    agent_file = tmp_path / "safe.py"
    agent_file.write_text(agent_code)

    # Make world-writable
    os.chmod(agent_file, 0o777)

    with pytest.raises(SecurityViolationError, match="world-writable"):
        load_agent_from_ref("safe.py:SafeAgent", root_dir=tmp_path)


# Test 3: Exfiltration Test
def test_exfiltration() -> None:
    # Construct a flow with a tool pointing to evil.com
    tool = ToolCapability(name="exfil_tool", url="http://api.evil.com/v1", risk_level="standard")
    pack = ToolPack(kind="ToolPack", namespace="test", tools=[tool], dependencies=[], env_vars=[])

    definitions = FlowDefinitions(tool_packs={"test_pack": pack}, profiles={})

    # Governance with allowlist
    governance = Governance(allowed_domains=["api.coreason.com"])

    metadata = FlowMetadata(name="test", version="1.0", description="test", tags=[])

    flow = LinearFlow(kind="LinearFlow", metadata=metadata, sequence=[], definitions=definitions, governance=governance)

    reports = validate_policy(flow)

    violation = next((r for r in reports if r.severity == "violation" and "blocked domain" in r.message), None)
    assert violation is not None
    assert violation.remediation is not None
    assert "api.evil.com" in violation.message
    assert violation.remediation.type == "whitelist_domain"


# Test 3b: Allowed URL Test (Coverage)
def test_allowed_url() -> None:
    # Construct a flow with a tool pointing to allowed domain
    tool = ToolCapability(name="safe_tool", url="http://api.coreason.com/v1", risk_level="standard")
    pack = ToolPack(kind="ToolPack", namespace="test", tools=[tool], dependencies=[], env_vars=[])

    definitions = FlowDefinitions(tool_packs={"test_pack": pack}, profiles={})

    governance = Governance(allowed_domains=["api.coreason.com"])

    metadata = FlowMetadata(name="test", version="1.0", description="test", tags=[])

    flow = LinearFlow(kind="LinearFlow", metadata=metadata, sequence=[], definitions=definitions, governance=governance)

    reports = validate_policy(flow)
    assert len(reports) == 0


# Test 4: Auto-Fix Test
def test_auto_fix() -> None:
    # Flow with critical capability but no guard

    # Create a critical tool.
    tool = ToolCapability(
        name="critical_tool", risk_level="critical", description="Dangerous tool", requires_approval=True
    )
    pack = ToolPack(kind="ToolPack", namespace="test", tools=[tool], dependencies=[], env_vars=[])

    definitions = FlowDefinitions(tool_packs={"test_pack": pack}, profiles={})

    node = AgentNode(
        id="unsafe_node",
        type="agent",
        profile="dummy_profile",  # String reference is enough if not validated against definitions for tool check
        tools=["critical_tool"],
        metadata={},
    )

    metadata = FlowMetadata(name="test", version="1.0", description="test", tags=[])

    # We set status="draft" so validate_referential_integrity doesn't complain about missing profile
    flow = LinearFlow(kind="LinearFlow", status="draft", metadata=metadata, sequence=[node], definitions=definitions)

    reports = validate_policy(flow)

    violation = next((r for r in reports if "requires high-risk features" in r.message), None)
    assert violation is not None
    assert violation.remediation is not None
    assert violation.remediation.type == "add_guard_node"
    assert violation.remediation.patch_data is not None
    # Ensure patch_data is a HumanNode dict
    patch = violation.remediation.patch_data
    assert patch["type"] == "human"
    assert patch["id"] == f"guard_{node.id}"


# Test 5: Circuit Breaker Logic
def test_circuit_breaker() -> None:
    policy = CircuitBreaker(error_threshold_count=5, reset_timeout_seconds=1)
    store: dict[str, CircuitState] = {}
    node_id = "node_1"

    # 1. Closed state (default) - should pass
    check_circuit(node_id, policy, store)
    assert store[node_id].state == "closed"

    # 2. Open the circuit manually
    store[node_id].state = "open"
    store[node_id].last_failure_time = time.time()

    # 3. Verify it raises CircuitOpenError immediately
    with pytest.raises(CircuitOpenError):
        check_circuit(node_id, policy, store)

    # 4. Wait for timeout
    time.sleep(1.1)

    # 5. Verify it transitions to half-open
    check_circuit(node_id, policy, store)
    assert store[node_id].state == "half-open"


# Test 6: Loader Error Handling and Cleanup
def test_loader_errors_and_cleanup(tmp_path: Path) -> None:
    # 1. Invalid reference format
    with pytest.raises(ValueError, match="Invalid reference format"):
        load_agent_from_ref("invalid_ref", root_dir=tmp_path)

    # 2. Syntax Error in file
    bad_code = "class Broken { "
    bad_file = tmp_path / "syntax.py"
    bad_file.write_text(bad_code)

    with pytest.raises(ValueError, match="Syntax error"):
        load_agent_from_ref("syntax.py:Broken", root_dir=tmp_path)

    # 3. Class not found
    empty_code = "x = 1"
    empty_file = tmp_path / "empty.py"
    empty_file.write_text(empty_code)

    with pytest.raises(ValueError, match="Agent class 'Missing' not found"):
        load_agent_from_ref("empty.py:Missing", root_dir=tmp_path)

    # 4. Not a class - Verify Cleanup
    var_code = "NotAClass = 123"
    var_file = tmp_path / "var.py"
    var_file.write_text(var_code)

    # Mock uuid to get a predictable module name
    mock_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    expected_module = f"coreason.dynamic.{mock_uuid}"

    with patch("uuid.uuid4", return_value=mock_uuid), pytest.raises(TypeError, match="is not a class"):
        load_agent_from_ref("var.py:NotAClass", root_dir=tmp_path)

    # ASSERT that the module was cleaned up
    assert expected_module not in sys.modules

    # 5. Runtime Error - Verify Cleanup
    runtime_code = """
class Ok: pass
1 / 0
"""
    runtime_file = tmp_path / "runtime.py"
    runtime_file.write_text(runtime_code)

    with patch("uuid.uuid4", return_value=mock_uuid), pytest.raises(ZeroDivisionError):
        load_agent_from_ref("runtime.py:Ok", root_dir=tmp_path)

    # ASSERT that the module was cleaned up
    assert expected_module not in sys.modules


# Test 7: Loader Success
def test_loader_success(tmp_path: Path) -> None:
    code = """
class MyAgent:
    def run(self):
        return "ok"
"""
    file = tmp_path / "success.py"
    file.write_text(code)

    agent_cls = load_agent_from_ref("success.py:MyAgent", root_dir=tmp_path)
    assert agent_cls.__name__ == "MyAgent"
    instance = agent_cls()
    assert instance.run() == "ok"
