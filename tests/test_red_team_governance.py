# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime
from typing import List, Optional, Union
from uuid import uuid4

from coreason_manifest.definitions.agent import (
    AgentCapability,
    AgentDefinition,
    AgentDependencies,
    AgentMetadata,
    AgentRuntimeConfig,
    CapabilityType,
    InlineToolDefinition,
    ModelConfig,
    ToolRequirement,
    ToolRiskLevel,
)
from coreason_manifest.definitions.topology import Edge, LogicNode, Node
from coreason_manifest.governance import GovernanceConfig, check_compliance


def create_agent(
    nodes: Optional[List[Node]] = None,
    edges: Optional[List[Edge]] = None,
    tools: Optional[List[Union[ToolRequirement, InlineToolDefinition]]] = None,
) -> AgentDefinition:
    metadata = AgentMetadata(
        id=uuid4(),
        version="1.0.0",
        name="Test Agent",
        author="Tester",
        created_at=datetime.now(),
    )

    capability = AgentCapability(
        name="test_cap",
        type=CapabilityType.ATOMIC,
        description="Test Capability",
        inputs={},
        outputs={},
    )

    config = AgentRuntimeConfig(
        nodes=nodes or [],
        edges=edges or [],
        entry_point=nodes[0].id if nodes else None,
        llm_config=ModelConfig(model="gpt-4", temperature=0.0),
    )

    dependencies = AgentDependencies(tools=tools or [])

    return AgentDefinition(
        metadata=metadata,
        capabilities=[capability],
        config=config,
        dependencies=dependencies,
    )


def test_logic_node_security_mitigation() -> None:
    """Mitigation: LogicNodes are now BLOCKED by default."""
    node = LogicNode(id="logic1", code="print('hack')")
    agent = create_agent(nodes=[node])
    config = GovernanceConfig()  # Defaults to allow_custom_logic=False
    report = check_compliance(agent, config)

    assert not report.passed, "LogicNode should be blocked by default"
    # Find violation
    logic_violations = [v for v in report.violations if v.rule == "custom_logic_restriction"]
    assert len(logic_violations) > 0, "Expected custom_logic_restriction violation"


def test_logic_node_allowed_explicitly() -> None:
    """Explicit Allow: LogicNodes allowed if config says so."""
    node = LogicNode(id="logic1", code="print('hack')")
    agent = create_agent(nodes=[node])
    config = GovernanceConfig(allow_custom_logic=True)
    report = check_compliance(agent, config)

    # Should pass logic check (assuming no other violations)
    assert report.passed, "LogicNode should be allowed if explicitly enabled"


def test_edge_condition_security_mitigation() -> None:
    """Mitigation: Conditional Edges are now BLOCKED by default."""
    node1 = LogicNode(id="start", code="pass")
    node2 = LogicNode(id="end", code="pass")
    edge = Edge(source_node_id="start", target_node_id="end", condition="True")

    # Note: LogicNode will also be blocked unless we only test edge.
    # But LogicNode is needed for valid graph?
    # Actually, check_compliance iterates nodes and edges separately.
    # But check_compliance will flag BOTH logic node AND edge condition.
    # Let's use allow_custom_logic=False (default).

    agent = create_agent(nodes=[node1, node2], edges=[edge])
    config = GovernanceConfig()
    report = check_compliance(agent, config)

    assert not report.passed
    # Should flag logic nodes AND edge condition
    # But wait, logic nodes are flagged too. So violation count > 0.
    # Let's verify specific violation for Edge.
    edge_violations = [v for v in report.violations if v.message.startswith("Edges with custom")]
    assert len(edge_violations) > 0, "Expected Edge condition violation"


def test_url_normalization_trailing_dot_strict() -> None:
    """Strict normalization handles trailing dots correctly."""
    tool = ToolRequirement(
        uri="https://example.com./api",  # Trailing dot
        hash="a" * 64,
        scopes=[],
        risk_level=ToolRiskLevel.SAFE,
    )
    agent = create_agent(tools=[tool])
    # allowed_domains without trailing dot
    config = GovernanceConfig(allowed_domains=["example.com"], strict_url_validation=True)
    report = check_compliance(agent, config)

    # Should PASS because strictly normalized "example.com." -> "example.com"
    assert report.passed, "Strict normalization should strip trailing dot and pass"


def test_url_normalization_case_insensitive() -> None:
    """Strict normalization handles case correctly."""
    tool = ToolRequirement(
        uri="https://Example.com/api",  # Mixed case
        hash="a" * 64,
        scopes=[],
        risk_level=ToolRiskLevel.SAFE,
    )
    agent = create_agent(tools=[tool])
    # allowed_domains lower case
    config = GovernanceConfig(allowed_domains=["example.com"], strict_url_validation=True)
    report = check_compliance(agent, config)

    assert report.passed, "Strict normalization should handle case"


def test_url_normalization_disabled_legacy() -> None:
    """Legacy behavior (strict=False) fails on trailing dot mismatch."""
    tool = ToolRequirement(
        uri="https://example.com./api",  # Trailing dot
        hash="a" * 64,
        scopes=[],
        risk_level=ToolRiskLevel.SAFE,
    )
    agent = create_agent(tools=[tool])
    # allowed_domains without trailing dot
    config = GovernanceConfig(allowed_domains=["example.com"], strict_url_validation=False)
    report = check_compliance(agent, config)

    # Should FAIL because no normalization happens on hostname (only lowercasing by urlparse)
    assert not report.passed
    assert report.violations[0].rule == "domain_restriction"
