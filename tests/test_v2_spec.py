# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.common import ToolRiskLevel
from coreason_manifest.v2.spec.definitions import (
    AgentDefinition,
    AgentStep,
    ManifestMetadata,
    ManifestV2,
    ToolDefinition,
    Workflow,
    SwitchStep,
)


@pytest.fixture
def base_manifest_kwargs() -> dict:
    return {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Test Manifest"},
    }


def test_integrity_valid(base_manifest_kwargs: dict) -> None:
    """Test a perfectly valid manifest."""
    tool = ToolDefinition(
        id="tool1",
        name="Tool",
        uri="https://example.com",
        risk_level=ToolRiskLevel.SAFE
    )
    agent = AgentDefinition(
        id="agent1",
        name="Agent",
        role="Role",
        goal="Goal",
        tools=["tool1"]
    )
    workflow = Workflow(
        start="step1",
        steps={
            "step1": AgentStep(id="step1", agent="agent1", next="step2"),
            "step2": AgentStep(id="step2", agent="agent1"),
        }
    )

    ManifestV2(
        workflow=workflow,
        definitions={"tool1": tool, "agent1": agent},
        **base_manifest_kwargs
    )


def test_integrity_failure_missing_tool(base_manifest_kwargs: dict) -> None:
    """Test integrity failure when an Agent references a non-existent Tool ID."""
    agent = AgentDefinition(
        id="agent1",
        name="Agent",
        role="Role",
        goal="Goal",
        tools=["missing-tool"]
    )
    workflow = Workflow(
        start="step1",
        steps={"step1": AgentStep(id="step1", agent="agent1")}
    )

    with pytest.raises(ValidationError, match="Agent 'agent1' references missing tool 'missing-tool'"):
        ManifestV2(
            workflow=workflow,
            definitions={"agent1": agent},
            **base_manifest_kwargs
        )


def test_integrity_failure_wrong_tool_type(base_manifest_kwargs: dict) -> None:
    """Test integrity failure when an Agent references a definition that is not a Tool."""
    agent1 = AgentDefinition(
        id="agent1",
        name="Agent 1",
        role="Role",
        goal="Goal",
        tools=["agent2"] # referencing another agent as a tool
    )
    agent2 = AgentDefinition(
        id="agent2",
        name="Agent 2",
        role="Role",
        goal="Goal"
    )
    workflow = Workflow(
        start="step1",
        steps={"step1": AgentStep(id="step1", agent="agent1")}
    )

    with pytest.raises(ValidationError, match="Agent 'agent1' references 'agent2' which is not a ToolDefinition"):
        ManifestV2(
            workflow=workflow,
            definitions={"agent1": agent1, "agent2": agent2},
            **base_manifest_kwargs
        )


def test_integrity_failure_missing_next_step(base_manifest_kwargs: dict) -> None:
    """Test integrity failure when a Step references a non-existent next ID."""
    agent = AgentDefinition(id="agent1", name="Agent", role="Role", goal="Goal")
    workflow = Workflow(
        start="step1",
        steps={
            "step1": AgentStep(id="step1", agent="agent1", next="missing-step")
        }
    )

    with pytest.raises(ValidationError, match="Step 'step1' references missing next step 'missing-step'"):
        ManifestV2(
            workflow=workflow,
            definitions={"agent1": agent},
            **base_manifest_kwargs
        )


def test_integrity_failure_missing_switch_target(base_manifest_kwargs: dict) -> None:
    """Test integrity failure when a SwitchStep references a non-existent step."""
    workflow = Workflow(
        start="switch1",
        steps={
            "switch1": SwitchStep(
                id="switch1",
                cases={"cond": "missing-case"},
                default="missing-default"
            )
        }
    )

    # It might fail on the first missing one it finds
    with pytest.raises(ValidationError, match="SwitchStep 'switch1' references missing step"):
        ManifestV2(
            workflow=workflow,
            definitions={},
            **base_manifest_kwargs
        )


def test_strictness_unknown_field_step() -> None:
    """Test that steps forbid unknown fields."""

    # We need to bypass the constructor validation or use a dict to trigger pydantic validation
    # But here we are instantiating the model directly.

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AgentStep(
            id="step1",
            agent="agent1",
            magic_parameter=True # type: ignore[call-arg]
        )


def test_strictness_unknown_field_agent_definition() -> None:
    """Test that AgentDefinition forbids unknown fields."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AgentDefinition(
            id="agent1",
            name="Agent",
            role="Role",
            goal="Goal",
            unknown_field="value" # type: ignore[call-arg]
        )


def test_agent_definition_tools_type() -> None:
    """Test that tools must be a list of strings."""
    with pytest.raises(ValidationError):
        AgentDefinition(
            id="agent1",
            name="Agent",
            role="Role",
            goal="Goal",
            tools=[123] # type: ignore[list-item]
        )
