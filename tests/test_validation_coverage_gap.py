# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from coreason_manifest import (
    AgentDefinition,
    AgentStep,
    CouncilStep,
    Manifest,
    ManifestMetadata,
    SwitchStep,
    ToolDefinition,
    ToolRequirement,
    ToolRiskLevel,
    Workflow,
    validate_loose,
)


def test_validate_loose_full_coverage() -> None:
    """Test validate_loose to cover all warning branches."""

    # Create definitions including wrong types for cross-referencing
    tool_def = ToolDefinition(id="tool1", name="Tool", uri="https://example.com", risk_level=ToolRiskLevel.SAFE)
    agent_def = AgentDefinition(
        id="agent1",
        name="Agent",
        role="Role",
        goal="Goal",
        tools=[ToolRequirement(uri="missing-tool"), ToolRequirement(uri="agent2")],
    )
    # agent2 is defined as an Agent, but if we use it as a tool in agent1, that triggers warning.
    # However, to test "Agent referencing non-Tool", we need agent1 to reference something that exists but isn't a tool.
    # Let's use 'agent2' which is an Agent.

    agent2_def = AgentDefinition(id="agent2", name="Agent 2", role="Role", goal="Goal")

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Broken Manifest"),
        definitions={
            "tool1": tool_def,
            "agent1": agent_def,
            "agent2": agent2_def,
        },
        workflow=Workflow(
            start="step1",
            steps={
                # 1. AgentStep next missing
                "step1": AgentStep(id="step1", agent="agent1", next="missing-next"),
                # 2. SwitchStep missing targets
                "step2": SwitchStep(
                    id="step2", cases={"cond": "missing-case-target"}, default="missing-default-target"
                ),
                # 3. AgentStep referencing missing agent
                "step3": AgentStep(id="step3", agent="missing-agent"),
                # 4. AgentStep referencing non-Agent (referencing tool1)
                "step4": AgentStep(id="step4", agent="tool1"),
                # 5. CouncilStep referencing missing voter
                "step5": CouncilStep(id="step5", voters=["missing-voter", "tool1"]),
            },
        ),
    )

    warnings = validate_loose(manifest)

    expected_warnings = [
        "Step 'step1' references missing next step 'missing-next'",
        "SwitchStep 'step2' references missing step 'missing-case-target' in cases",
        "SwitchStep 'step2' references missing step 'missing-default-target' in default",
        "AgentStep 'step3' references missing agent 'missing-agent'",
        "AgentStep 'step4' references 'tool1' which is not an AgentDefinition",
        "CouncilStep 'step5' references missing voter 'missing-voter'",
        "CouncilStep 'step5' references voter 'tool1' which is not an AgentDefinition",
        "Agent 'agent1' references missing tool 'missing-tool'",
        "Agent 'agent1' references 'agent2' which is not a ToolDefinition",
    ]

    for expected in expected_warnings:
        assert any(expected in w for w in warnings), f"Missing warning: {expected}"
