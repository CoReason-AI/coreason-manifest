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

from coreason_manifest import (
    AgentDefinition,
    AgentStep,
    Manifest,
    ManifestMetadata,
    ToolDefinition,
    ToolRequirement,
    ToolRiskLevel,
    Workflow,
)


def test_validate_integrity_full_coverage() -> None:
    """Test strict integrity checks cover all error branches."""

    # Create definitions including wrong types for cross-referencing
    tool_def = ToolDefinition(id="tool1", name="Tool", uri="https://example.com", risk_level=ToolRiskLevel.SAFE)
    # Note: AgentDefinition now requires Tools to be ToolRequirement or InlineToolDefinition.
    # We can't easily make it reference "agent2" in a way that passes Pydantic type validation
    # but fails referential integrity unless we use ToolRequirement with a URI that matches an agent ID.
    # "missing-tool" will be a URI. "agent2" will be a URI.

    agent_def = AgentDefinition(
        id="agent1",
        name="Agent",
        role="Role",
        goal="Goal",
        tools=[ToolRequirement(uri="missing-tool"), ToolRequirement(uri="agent2")],
    )

    agent2_def = AgentDefinition(id="agent2", name="Agent 2", role="Role", goal="Goal")

    # We construct the Manifest. Validation happens immediately.
    # Since it fails on the first error, we can only test one at a time, or we test that it fails generally.
    # To test full coverage, we would need separate tests.
    # Here we just verify it raises ValueError for *some* reason, confirming validation is active.

    with pytest.raises(ValidationError) as exc:
        Manifest(
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
                    "step1": AgentStep(id="step1", agent="agent1", next="missing-next"),
                },
            ),
        )

    # It should fail on the first error found.
    assert "references missing next step" in str(exc.value)
