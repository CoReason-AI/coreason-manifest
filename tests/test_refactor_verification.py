import pytest

from coreason_manifest.spec.core.flow import AgentNode, LinearFlow
from coreason_manifest.spec.core.flow import FlowDefinitions as Definitions
from coreason_manifest.spec.core.governance import CircuitBreaker, Governance
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.utils.gatekeeper import validate_policy
from coreason_manifest.utils.integrity import compute_hash, reconstruct_payload, verify_merkle_proof
from coreason_manifest.utils.io import SecurityViolationError
from coreason_manifest.utils.loader import load_agent_from_ref

# ------------------------------------------------------------------------
# 1. Malicious Agent Test (Loader Security)
# ------------------------------------------------------------------------


def test_malicious_agent_ast_check(tmp_path):
    """
    Creating a Python agent with `import subprocess` MUST raise a SecurityViolationError.
    """
    malicious_code = """
import subprocess

class Agent:
    def run(self):
        subprocess.call(["ls", "-la"])
"""
    agent_file = tmp_path / "evil_agent.py"
    agent_file.write_text(malicious_code)

    # We expect a SecurityViolationError from the loader's AST check
    with pytest.raises(SecurityViolationError, match="Security"):
        load_agent_from_ref(f"{agent_file}:Agent", root_dir=tmp_path)


def test_malicious_gadget_chain(tmp_path):
    """
    Test that gadget chains like object.__subclasses__ are blocked.
    """
    gadget_code = """
class Agent:
    def run(self):
        # Classic gadget chain attempt
        return [c for c in ().__class__.__bases__[0].__subclasses__() if c.__name__ == 'Popen']
"""
    agent_file = tmp_path / "gadget.py"
    agent_file.write_text(gadget_code)

    with pytest.raises(SecurityViolationError, match="Security"):
        load_agent_from_ref(f"{agent_file}:Agent", root_dir=tmp_path)


# ------------------------------------------------------------------------
# 2. Permissions Test (ManifestIO)
# ------------------------------------------------------------------------


def test_permissions_world_writable(tmp_path):
    """
    Loading a valid agent from a world-writable file MUST fail on POSIX systems.
    """
    import sys

    if sys.platform == "win32":
        pytest.skip("Skipping permissions test on Windows")

    valid_code = """
class Agent:
    pass
"""
    agent_file = tmp_path / "good_agent.py"
    agent_file.write_text(valid_code)

    # Make it world writable (0o777)
    agent_file.chmod(0o777)

    with pytest.raises(SecurityViolationError, match="world-writable"):
        load_agent_from_ref(f"{agent_file}:Agent", root_dir=tmp_path)


# ------------------------------------------------------------------------
# 3. Exfiltration Test (Gatekeeper Domain Policy)
# ------------------------------------------------------------------------


def test_exfiltration_blocked_domain():
    """
    A tool pointing to `api.evil.com` must trigger a validation error
    if `allowed_domains=["api.coreason.com"]` is set.
    """
    gov = Governance(allowed_domains=["api.coreason.com"])

    # Tool pointing to evil.com
    tool = ToolCapability(
        name="EvilTool", risk_level="standard", description="Steals data", url="https://api.evil.com/v1/steal"
    )

    flow = LinearFlow(
        kind="LinearFlow",
        metadata={"name": "test", "version": "1.0", "description": "test", "tags": []},
        governance=gov,
        definitions=Definitions(
            tool_packs={
                "default": ToolPack(kind="ToolPack", namespace="default", tools=[tool], dependencies=[], env_vars=[])
            }
        ),
        sequence=[AgentNode(id="agent1", metadata={}, type="agent", profile="p1", tools=["EvilTool"])],
    )

    reports = validate_policy(flow)

    violation = next((r for r in reports if r.severity == "violation" and "blocked domain" in r.message), None)
    assert violation is not None
    assert "api.evil.com" in violation.message
    assert violation.remediation.type == "whitelist_domain"


def test_allowed_url():
    """
    A tool pointing to a valid domain should pass.
    """
    gov = Governance(allowed_domains=["api.coreason.com"])

    tool = ToolCapability(
        name="GoodTool", risk_level="standard", description="Safe", url="https://api.coreason.com/v1/data"
    )

    flow = LinearFlow(
        kind="LinearFlow",
        metadata={"name": "test", "version": "1.0", "description": "test", "tags": []},
        governance=gov,
        definitions=Definitions(
            tool_packs={
                "default": ToolPack(kind="ToolPack", namespace="default", tools=[tool], dependencies=[], env_vars=[])
            }
        ),
        sequence=[AgentNode(id="agent1", metadata={}, type="agent", profile="p1", tools=["GoodTool"])],
    )

    reports = validate_policy(flow)
    violations = [r for r in reports if r.severity == "violation"]
    assert len(violations) == 0

    # Test subdomain allow
    # Using model_copy to update frozen instance
    tool_sub = tool.model_copy(update={"url": "https://sub.api.coreason.com/v1"})

    flow_sub = LinearFlow(
        kind="LinearFlow",
        metadata={"name": "test", "version": "1.0", "description": "test", "tags": []},
        governance=gov,
        definitions=Definitions(
            tool_packs={
                "default": ToolPack(
                    kind="ToolPack", namespace="default", tools=[tool_sub], dependencies=[], env_vars=[]
                )
            }
        ),
        sequence=[AgentNode(id="agent1", metadata={}, type="agent", profile="p1", tools=["GoodTool"])],
    )
    reports = validate_policy(flow_sub)
    assert len([r for r in reports if r.severity == "violation"]) == 0


def test_schemeless_url_handling():
    """
    Test that schemeless URLs (evil.com/google.com) are parsed correctly.
    """
    gov = Governance(allowed_domains=["google.com"])

    # This URL looks like it might be google.com if naive parsing is used,
    # but strictly it is evil.com/google.com
    tool = ToolCapability(name="TrickyTool", risk_level="standard", description="Tricky", url="evil.com/google.com")

    flow = LinearFlow(
        kind="LinearFlow",
        metadata={"name": "test", "version": "1.0", "description": "test", "tags": []},
        governance=gov,
        definitions=Definitions(
            tool_packs={
                "default": ToolPack(kind="ToolPack", namespace="default", tools=[tool], dependencies=[], env_vars=[])
            }
        ),
        sequence=[AgentNode(id="agent1", metadata={}, type="agent", profile="p1", tools=["TrickyTool"])],
    )

    reports = validate_policy(flow)
    violation = next((r for r in reports if r.severity == "violation" and "blocked domain" in r.message), None)

    # Should detect evil.com
    assert violation is not None
    assert "evil.com" in violation.message


# ------------------------------------------------------------------------
# 4. Auto-Fix Test (Gatekeeper Remediation)
# ------------------------------------------------------------------------


def test_auto_fix_computer_use():
    """
    A graph with an unguarded "Computer Use" node must return a validation report
    containing a JSON patch to insert a HumanNode.
    """
    # Create a profile that requires computer_use
    from coreason_manifest.spec.core.engines import ComputerUseReasoning
    from coreason_manifest.spec.core.nodes import CognitiveProfile as Profile

    # Use actual engine that requires computer_use
    reasoning = ComputerUseReasoning(model="gpt-4")

    profile = Profile(role="hacker", persona="hacker", reasoning=reasoning, fast_path=None)

    flow = LinearFlow(
        kind="LinearFlow",
        metadata={"name": "unsafe", "version": "1.0", "description": "unsafe", "tags": []},
        definitions=Definitions(profiles={"hacker": profile}),
        sequence=[AgentNode(id="attacker", metadata={}, type="agent", profile="hacker", tools=[])],
    )

    reports = validate_policy(flow)

    violation = next((r for r in reports if "computer_use capability" in r.message), None)
    assert violation is not None
    assert violation.remediation.type == "add_guard_node"
    assert violation.remediation.format == "json_patch"

    patch = violation.remediation.patch_data
    assert isinstance(patch, list)
    assert patch[0]["op"] == "add"
    assert patch[0]["value"]["type"] == "human"


def test_verify_remediation_patch_structure():
    """
    Verify that the remediation patch is a valid JSON Patch structure.
    """
    # ... setup same as above ...
    from coreason_manifest.spec.core.engines import CodeExecutionReasoning
    from coreason_manifest.spec.core.nodes import CognitiveProfile as Profile

    reasoning = CodeExecutionReasoning(model="gpt-4")

    profile = Profile(role="coder", persona="coder", reasoning=reasoning, fast_path=None)

    flow = LinearFlow(
        kind="LinearFlow",
        metadata={"name": "unsafe", "version": "1.0", "description": "unsafe", "tags": []},
        definitions=Definitions(profiles={"coder": profile}),
        sequence=[AgentNode(id="coder_agent", metadata={}, type="agent", profile="coder", tools=[])],
    )

    reports = validate_policy(flow)
    violation = next(r for r in reports if "code_execution" in r.message)

    # Check structure
    patch = violation.remediation.patch_data
    assert len(patch) == 1
    op = patch[0]
    assert "op" in op
    assert op["op"] == "add"
    assert "path" in op
    assert "value" in op


# ------------------------------------------------------------------------
# 5. Circuit Breaker Test
# ------------------------------------------------------------------------


def test_circuit_breaker_logic():
    """
    Test CircuitState transitions and enforcement.
    """
    from coreason_manifest.spec.core.governance import (
        CircuitOpenError,
        check_circuit,
        record_failure,
        record_success,
    )

    cb = CircuitBreaker(error_threshold_count=2, reset_timeout_seconds=1)
    # We don't manually create state, functions handle it.
    store = {}
    node_id = "node1"

    # 1. Closed State - OK
    check_circuit(node_id, cb, store)

    # 2. Record Failures
    record_failure(node_id, cb, store)  # count=1
    check_circuit(node_id, cb, store)  # Still closed

    record_failure(node_id, cb, store)  # count=2 -> Open

    # 3. Verify Open
    with pytest.raises(CircuitOpenError):
        check_circuit(node_id, cb, store)

    # 4. Wait for timeout
    import time

    time.sleep(1.1)

    # 5. Half-Open
    check_circuit(node_id, cb, store)  # Should pass (Half-Open)
    state = store[node_id]
    assert state.state == "half-open"

    # 6. Success -> Closed
    record_success(node_id, store)
    assert state.state == "closed"
    assert state.failure_count == 0


# ------------------------------------------------------------------------
# 6. Strict Integrity Test
# ------------------------------------------------------------------------


def test_strict_integrity():
    """
    Verify strict Merkle proof verification.
    """
    # 1. Valid Chain
    # We must construct payload exactly as reconstruct_payload does to get matching hashes.
    # reconstruct_payload adds 'attributes': {} and sorts 'previous_hashes'

    data1_raw = {"node_id": "n1", "state": "success", "previous_hashes": []}
    # Use reconstruct_payload to normalize before hashing, to match verification logic
    payload1 = reconstruct_payload(data1_raw)
    h1 = compute_hash(payload1)

    node1 = data1_raw.copy()
    node1["execution_hash"] = h1

    data2_raw = {"node_id": "n2", "state": "success", "previous_hashes": [h1]}
    payload2 = reconstruct_payload(data2_raw)
    h2 = compute_hash(payload2)

    node2 = data2_raw.copy()
    node2["execution_hash"] = h2

    trace = [node1, node2]
    assert verify_merkle_proof(trace) is True

    # 2. Tampered Content
    node1_tampered = node1.copy()
    node1_tampered["state"] = "failed"  # changed content
    trace_tampered = [node1_tampered, node2]
    assert verify_merkle_proof(trace_tampered) is False

    # 3. Broken Link
    node2_broken = node2.copy()
    node2_broken["previous_hashes"] = ["wrong_hash"]
    trace_broken = [node1, node2_broken]
    assert verify_merkle_proof(trace_broken) is False
