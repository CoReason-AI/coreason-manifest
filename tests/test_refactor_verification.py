import os
import sys
import time
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
    record_failure,
    record_success,
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

    # 3. Submodule Bypass
    code_sub = "import os.path"
    file_sub = tmp_path / "bypass.py"
    file_sub.write_text(code_sub)
    with pytest.raises(SecurityViolationError, match=r"Banned import 'os\.path'"):
        load_agent_from_ref("bypass.py:Agent", root_dir=tmp_path)

    # 4. Dangerous Calls
    for call in ["__import__('os')", "eval('1')", "exec('print(1)')", "compile('1', '', 'exec')"]:
        code_call = f"x = {call}"
        file_call = tmp_path / f"call_{call[:4]}.py"
        file_call.write_text(code_call)
        with pytest.raises(SecurityViolationError, match="Banned call"):
            load_agent_from_ref(f"{file_call.name}:Agent", root_dir=tmp_path)


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


# Test 3b: Allowed URL Test (Coverage & Edge Cases)
def test_allowed_url() -> None:
    # Construct a flow with a tool pointing to allowed domain
    tool = ToolCapability(name="safe_tool", url="http://api.coreason.com/v1", risk_level="standard")
    pack = ToolPack(kind="ToolPack", namespace="test", tools=[tool], dependencies=[], env_vars=[])

    definitions = FlowDefinitions(tool_packs={"test_pack": pack}, profiles={})

    governance = Governance(allowed_domains=["api.coreason.com", "google.com"])

    metadata = FlowMetadata(name="test", version="1.0", description="test", tags=[])

    flow = LinearFlow(kind="LinearFlow", metadata=metadata, sequence=[], definitions=definitions, governance=governance)

    reports = validate_policy(flow)
    assert len(reports) == 0

    # Schemeless URL check
    tool_schemeless = tool.model_copy(update={"url": "google.com/search"})
    assert flow.definitions is not None
    flow.definitions.tool_packs["test_pack"].tools[0] = tool_schemeless
    reports = validate_policy(flow)
    assert len(reports) == 0

    # Schemeless Blocked
    tool_blocked = tool.model_copy(update={"url": "evil.com/foo"})
    assert flow.definitions is not None
    flow.definitions.tool_packs["test_pack"].tools[0] = tool_blocked
    reports = validate_policy(flow)
    assert len(reports) == 1
    assert "evil.com" in reports[0].message


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


def test_circuit_breaker_state_updates() -> None:
    policy = CircuitBreaker(error_threshold_count=2, reset_timeout_seconds=1)
    store: dict[str, CircuitState] = {}
    node_id = "n1"

    # Fail 1
    record_failure(node_id, policy, store)
    assert store[node_id].state == "closed"
    assert store[node_id].failure_count == 1

    # Fail 2 (Threshold)
    record_failure(node_id, policy, store)
    assert store[node_id].state == "open"

    # Check
    with pytest.raises(CircuitOpenError):
        check_circuit(node_id, policy, store)

    # Test early return in record_failure when already open
    # failure_count should NOT increment
    count_before = store[node_id].failure_count
    record_failure(node_id, policy, store)
    assert store[node_id].failure_count == count_before

    # Wait for timeout (simulated by updating time)
    last_failure = store[node_id].last_failure_time
    assert last_failure is not None
    store[node_id].last_failure_time = last_failure - 2

    # Check (Half-Open)
    check_circuit(node_id, policy, store)
    assert store[node_id].state == "half-open"

    # Success
    record_success(node_id, store)
    assert store[node_id].state == "closed"
    assert store[node_id].failure_count == 0


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

    # 4. Not a class - Verify Cleanup logic (should not raise KeyError)
    var_code = "NotAClass = 123"
    var_file = tmp_path / "var.py"
    var_file.write_text(var_code)

    # In the new implementation, we don't inject into sys.modules, so checking it is not relevant for pollution
    # But we want to ensure it fails with correct error
    with pytest.raises(TypeError, match="is not a class"):
        load_agent_from_ref("var.py:NotAClass", root_dir=tmp_path)

    # 5. Runtime Error - Verify Exception
    runtime_code = """
class Ok: pass
1 / 0
"""
    runtime_file = tmp_path / "runtime.py"
    runtime_file.write_text(runtime_code)

    with pytest.raises(ValueError, match="Failed to execute"):
        load_agent_from_ref("runtime.py:Ok", root_dir=tmp_path)

    # 6. Spec Creation Failure
    # Difficult to trigger via spec_from_file_location with valid path,
    # but we can mock it to return None
    with (
        patch("importlib.util.spec_from_file_location", return_value=None),
        pytest.raises(ValueError, match="Could not create module spec"),
    ):
        load_agent_from_ref("runtime.py:Ok", root_dir=tmp_path)


# Test 7: Loader Success & Hygiene
def test_loader_success_hygiene(tmp_path: Path) -> None:
    code = """
class MyAgent:
    def run(self):
        return "ok"
"""
    file = tmp_path / "success.py"
    file.write_text(code)

    # Check sys.path/modules before
    orig_path = list(sys.path)
    orig_modules = set(sys.modules.keys())

    agent_cls = load_agent_from_ref("success.py:MyAgent", root_dir=tmp_path)
    assert agent_cls.__name__ == "MyAgent"
    instance = agent_cls()
    assert instance.run() == "ok"

    # Verify Hygiene
    assert sys.path == orig_path

    # Verify module is NOT leaked in sys.modules
    current_modules = set(sys.modules.keys())
    diff = current_modules - orig_modules
    for m in diff:
        assert "success" not in m
        assert "coreason.dynamic" not in m


# Test 8: System Pollution Verification (Ensuring previous tests didn't leak)
def test_sys_pollution_check() -> None:
    # This is a meta-check to ensure previous tests cleaned up
    # Since loader now avoids sys.modules, there should be no coreason.dynamic modules
    modules = [m for m in sys.modules if "coreason.dynamic" in m]
    assert len(modules) == 0, f"Leaked modules found: {modules}"
