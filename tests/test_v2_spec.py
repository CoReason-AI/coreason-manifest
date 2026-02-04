# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict

import pytest
from pydantic import ValidationError

from coreason_manifest.common import ToolRiskLevel
from coreason_manifest.v2.spec.definitions import (
    AgentDefinition,
    AgentStep,
    ManifestV2,
    SwitchStep,
    ToolDefinition,
    Workflow,
)
from coreason_manifest.v2.validator import validate_integrity


@pytest.fixture
def base_manifest_kwargs() -> Dict[str, Any]:
    return {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Test Manifest"},
    }


def test_integrity_valid(base_manifest_kwargs: Dict[str, Any]) -> None:
    """Test a perfectly valid manifest."""
    tool = ToolDefinition(id="tool1", name="Tool", uri="https://example.com", risk_level=ToolRiskLevel.SAFE)
    agent = AgentDefinition(id="agent1", name="Agent", role="Role", goal="Goal", tools=["tool1"])
    workflow = Workflow(
        start="step1",
        steps={
            "step1": AgentStep(id="step1", agent="agent1", next="step2"),
            "step2": AgentStep(id="step2", agent="agent1"),
        },
    )

    manifest = ManifestV2(workflow=workflow, definitions={"tool1": tool, "agent1": agent}, **base_manifest_kwargs)
    validate_integrity(manifest)


def test_integrity_failure_missing_tool(base_manifest_kwargs: Dict[str, Any]) -> None:
    """Test integrity failure when an Agent references a non-existent Tool ID."""
    agent = AgentDefinition(id="agent1", name="Agent", role="Role", goal="Goal", tools=["missing-tool"])
    workflow = Workflow(start="step1", steps={"step1": AgentStep(id="step1", agent="agent1")})

    manifest = ManifestV2(workflow=workflow, definitions={"agent1": agent}, **base_manifest_kwargs)

    with pytest.raises(ValueError, match="Agent 'agent1' references missing tool 'missing-tool'"):
        validate_integrity(manifest)


def test_integrity_failure_wrong_tool_type(base_manifest_kwargs: Dict[str, Any]) -> None:
    """Test integrity failure when an Agent references a definition that is not a Tool."""
    agent1 = AgentDefinition(
        id="agent1",
        name="Agent 1",
        role="Role",
        goal="Goal",
        tools=["agent2"],  # referencing another agent as a tool
    )
    agent2 = AgentDefinition(id="agent2", name="Agent 2", role="Role", goal="Goal")
    workflow = Workflow(start="step1", steps={"step1": AgentStep(id="step1", agent="agent1")})

    manifest = ManifestV2(workflow=workflow, definitions={"agent1": agent1, "agent2": agent2}, **base_manifest_kwargs)

    with pytest.raises(ValueError, match="Agent 'agent1' references 'agent2' which is not a ToolDefinition"):
        validate_integrity(manifest)


def test_integrity_failure_missing_next_step(base_manifest_kwargs: Dict[str, Any]) -> None:
    """Test integrity failure when a Step references a non-existent next ID."""
    agent = AgentDefinition(id="agent1", name="Agent", role="Role", goal="Goal")
    workflow = Workflow(start="step1", steps={"step1": AgentStep(id="step1", agent="agent1", next="missing-step")})

    manifest = ManifestV2(workflow=workflow, definitions={"agent1": agent}, **base_manifest_kwargs)

    with pytest.raises(ValueError, match="Step 'step1' references missing next step 'missing-step'"):
        validate_integrity(manifest)


def test_integrity_failure_missing_switch_target(base_manifest_kwargs: Dict[str, Any]) -> None:
    """Test integrity failure when a SwitchStep references a non-existent step."""
    workflow = Workflow(
        start="switch1",
        steps={"switch1": SwitchStep(id="switch1", cases={"cond": "missing-case"}, default="missing-default")},
    )

    manifest = ManifestV2(workflow=workflow, definitions={}, **base_manifest_kwargs)

    # It might fail on the first missing one it finds
    with pytest.raises(ValueError, match="SwitchStep 'switch1' references missing step"):
        validate_integrity(manifest)


def test_strictness_unknown_field_step() -> None:
    """Test that steps forbid unknown fields."""

    # We need to bypass the constructor validation or use a dict to trigger pydantic validation
    # But here we are instantiating the model directly.

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AgentStep(
            id="step1",
            agent="agent1",
            magic_parameter=True,  # type: ignore[call-arg]
        )


def test_strictness_unknown_field_agent_definition() -> None:
    """Test that AgentDefinition forbids unknown fields."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AgentDefinition(
            id="agent1",
            name="Agent",
            role="Role",
            goal="Goal",
            unknown_field="value",  # type: ignore[call-arg]
        )


def test_agent_definition_tools_type() -> None:
    """Test that tools must be a list of strings."""
    with pytest.raises(ValidationError):
        # We need to construct this such that mypy is happy but Pydantic runtime fails
        # Mypy checks list contents, but casting can bypass it if needed
        # However, here we are testing runtime behavior.
        # If mypy is not complaining locally but CI is complaining about unused ignore, it means environment diff.
        # Let's try casting to Any to bypass Mypy completely, then validation happens at runtime.
        from typing import Any, cast

        bad_tools = cast(Any, [123])
        AgentDefinition(
            id="agent1",
            name="Agent",
            role="Role",
            goal="Goal",
            tools=bad_tools,
        )


def test_manifest_serialization(base_manifest_kwargs: Dict[str, Any]) -> None:
    """Test that ManifestV2 serializes correctly, especially Enums."""
    tool = ToolDefinition(id="tool1", name="Tool", uri="https://example.com", risk_level=ToolRiskLevel.SAFE)
    manifest = ManifestV2(
        workflow=Workflow(
            start="step1",
            steps={"step1": AgentStep(id="step1", agent="agent1")},
        ),
        definitions={
            "tool1": tool,
            "agent1": AgentDefinition(id="agent1", name="Agent", role="Role", goal="Goal", tools=["tool1"]),
        },
        **base_manifest_kwargs,
    )

    dumped = manifest.dump()

    # Assert risk_level is serialized to string
    # We must access it via the definitions dict
    # Note: ManifestV2 definitions values are Union[Union[ToolDefinition, AgentDefinition], GenericDefinition]
    # But when dumped, it is a dict of dicts.
    assert dumped["definitions"]["tool1"]["risk_level"] == "safe"
    assert isinstance(dumped["definitions"]["tool1"]["risk_level"], str)
