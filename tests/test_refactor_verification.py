import os
from pathlib import Path

import pytest

from coreason_manifest.spec.core.flow import FlowDefinitions, FlowMetadata, LinearFlow
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.utils.gatekeeper import validate_policy
from coreason_manifest.utils.loader import SecurityViolationError, load_agent_from_ref


# Test 1: Malicious Agent (AST check)
def test_malicious_agent_ast(tmp_path: Path) -> None:
    # Create a malicious agent file
    agent_code = """
import os

class MaliciousAgent:
    def run(self):
        os.system("echo 'pwned'")
"""
    agent_file = tmp_path / "malicious.py"
    agent_file.write_text(agent_code)

    with pytest.raises(SecurityViolationError, match="Banned import 'os'"):
        load_agent_from_ref("malicious.py:MaliciousAgent", root_dir=tmp_path)


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
