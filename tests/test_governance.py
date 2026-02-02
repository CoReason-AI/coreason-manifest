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
from uuid import uuid4
from typing import List, Optional, Union

from coreason_manifest.definitions.agent import (
    AgentDefinition,
    AgentMetadata,
    AgentCapability,
    CapabilityType,
    AgentRuntimeConfig,
    AgentDependencies,
    ToolRequirement,
    ToolRiskLevel,
    InlineToolDefinition,
    ModelConfig
)
from unittest.mock import patch
from coreason_manifest.governance import check_compliance, GovernanceConfig

ToolType = Union[ToolRequirement, InlineToolDefinition]

# Helper to create a minimal valid AgentDefinition
def create_agent(
    tools: Optional[List[ToolType]] = None,
    requires_auth: bool = False
) -> AgentDefinition:
    if tools is None:
        tools = []

    metadata = AgentMetadata(
        id=uuid4(),
        version="1.0.0",
        name="Test Agent",
        author="Test Author",
        created_at=datetime.now(),
        requires_auth=requires_auth
    )

    # Capabilitiy needs to inject user_context if auth is required
    injected_params = ["user_context"] if requires_auth else []

    capability = AgentCapability(
        name="chat",
        type=CapabilityType.ATOMIC,
        description="Chat capability",
        inputs={},
        outputs={},
        injected_params=injected_params
    )

    config = AgentRuntimeConfig(
        llm_config=ModelConfig(
            model="gpt-4",
            temperature=0.7,
            system_prompt="You are a helpful assistant."
        )
    )

    dependencies = AgentDependencies(
        tools=tools
    )

    return AgentDefinition(
        metadata=metadata,
        capabilities=[capability],
        config=config,
        dependencies=dependencies
    )

def test_governance_no_restrictions() -> None:
    agent = create_agent()
    config = GovernanceConfig()
    report = check_compliance(agent, config)
    assert report.passed
    assert len(report.violations) == 0

def test_governance_domain_restriction_pass() -> None:
    tool = ToolRequirement(
        uri="https://trusted.com/tool",
        hash="a" * 64,
        scopes=[],
        risk_level=ToolRiskLevel.SAFE
    )
    agent = create_agent(tools=[tool])
    config = GovernanceConfig(allowed_domains=["trusted.com"])
    report = check_compliance(agent, config)
    assert report.passed

def test_governance_domain_restriction_fail() -> None:
    tool = ToolRequirement(
        uri="https://untrusted.com/tool",
        hash="a" * 64,
        scopes=[],
        risk_level=ToolRiskLevel.SAFE
    )
    agent = create_agent(tools=[tool])
    config = GovernanceConfig(allowed_domains=["trusted.com"])
    report = check_compliance(agent, config)
    assert not report.passed
    assert len(report.violations) == 1
    assert report.violations[0].rule == "domain_restriction"

def test_governance_risk_level_pass() -> None:
    tool = ToolRequirement(
        uri="https://example.com/tool",
        hash="a" * 64,
        scopes=[],
        risk_level=ToolRiskLevel.SAFE
    )
    agent = create_agent(tools=[tool])
    config = GovernanceConfig(max_risk_level=ToolRiskLevel.STANDARD)
    report = check_compliance(agent, config)
    assert report.passed

def test_governance_risk_level_fail() -> None:
    tool = ToolRequirement(
        uri="https://example.com/tool",
        hash="a" * 64,
        scopes=[],
        risk_level=ToolRiskLevel.CRITICAL
    )
    agent = create_agent(tools=[tool])
    config = GovernanceConfig(max_risk_level=ToolRiskLevel.STANDARD)
    report = check_compliance(agent, config)
    assert not report.passed
    assert report.violations[0].rule == "risk_level_restriction"

def test_governance_auth_check_pass() -> None:
    # Critical tool, but agent requires auth
    tool = ToolRequirement(
        uri="https://example.com/tool",
        hash="a" * 64,
        scopes=[],
        risk_level=ToolRiskLevel.CRITICAL
    )
    agent = create_agent(tools=[tool], requires_auth=True)
    config = GovernanceConfig(require_auth_for_critical_tools=True)
    report = check_compliance(agent, config)
    assert report.passed

def test_governance_auth_check_fail() -> None:
    # Critical tool, agent does NOT require auth
    tool = ToolRequirement(
        uri="https://example.com/tool",
        hash="a" * 64,
        scopes=[],
        risk_level=ToolRiskLevel.CRITICAL
    )
    agent = create_agent(tools=[tool], requires_auth=False)
    config = GovernanceConfig(require_auth_for_critical_tools=True)
    report = check_compliance(agent, config)
    assert not report.passed
    assert report.violations[0].rule == "auth_requirement"

def test_governance_inline_tool_ignored() -> None:
    # Inline tool has no URI or risk level, should be ignored
    tool = InlineToolDefinition(
        name="inline_tool",
        description="Inline",
        parameters={}
    )
    agent = create_agent(tools=[tool])
    config = GovernanceConfig(
        allowed_domains=["trusted.com"],
        max_risk_level=ToolRiskLevel.SAFE
    )
    report = check_compliance(agent, config)
    assert report.passed

def test_governance_multiple_violations() -> None:
    tool1 = ToolRequirement(
        uri="https://untrusted.com/tool",
        hash="a" * 64,
        scopes=[],
        risk_level=ToolRiskLevel.CRITICAL
    )
    agent = create_agent(tools=[tool1], requires_auth=False)
    config = GovernanceConfig(
        allowed_domains=["trusted.com"],
        max_risk_level=ToolRiskLevel.STANDARD,
        require_auth_for_critical_tools=True
    )
    report = check_compliance(agent, config)
    assert not report.passed
    # Should fail domain, risk, and auth
    rules = [v.rule for v in report.violations]
    assert "domain_restriction" in rules
    assert "risk_level_restriction" in rules
    assert "auth_requirement" in rules
    assert len(rules) == 3

def test_governance_malformed_uri_handling() -> None:
    tool = ToolRequirement(
        uri="https://example.com/tool",
        hash="a" * 64,
        scopes=[],
        risk_level=ToolRiskLevel.SAFE
    )
    agent = create_agent(tools=[tool])
    config = GovernanceConfig(allowed_domains=["trusted.com"])

    with patch("coreason_manifest.governance.urlparse", side_effect=ValueError("Mock Error")):
        report = check_compliance(agent, config)

    assert not report.passed
    assert len(report.violations) == 1
    assert report.violations[0].rule == "domain_restriction"
    assert "Failed to parse tool URI" in report.violations[0].message
