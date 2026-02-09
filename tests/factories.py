# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    InlineToolDefinition,
    ManifestV2,
    ToolDefinition,
    Workflow,
)
from coreason_manifest.spec.common_base import ToolRiskLevel


def create_agent_definition(
    id: str = "agent-1",
    name: str = "Test Agent",
    role: str = "Tester",
    goal: str = "Test things",
    **kwargs: Any,
) -> AgentDefinition:
    """Factory for AgentDefinition."""
    defaults = {
        "type": "agent",
        "id": id,
        "name": name,
        "role": role,
        "goal": goal,
    }
    defaults.update(kwargs)
    return AgentDefinition(**defaults)


def create_tool_definition(
    id: str = "tool-1",
    name: str = "Test Tool",
    uri: str = "https://example.com/tool",
    risk_level: ToolRiskLevel = ToolRiskLevel.SAFE,
    **kwargs: Any,
) -> ToolDefinition:
    """Factory for ToolDefinition."""
    defaults = {
        "type": "tool",
        "id": id,
        "name": name,
        "uri": uri,
        "risk_level": risk_level,
    }
    defaults.update(kwargs)
    return ToolDefinition(**defaults)


def create_inline_tool_definition(
    name: str = "inline_tool",
    description: str = "Does something",
    parameters: dict[str, Any] | None = None,
    **kwargs: Any,
) -> InlineToolDefinition:
    """Factory for InlineToolDefinition."""
    if parameters is None:
        parameters = {"type": "object", "properties": {}}

    defaults = {
        "type": "inline",
        "name": name,
        "description": description,
        "parameters": parameters,
    }
    defaults.update(kwargs)
    return InlineToolDefinition(**defaults)


def create_workflow(start: str = "step-1", steps: dict[str, Any] | None = None) -> Workflow:
    """Factory for Workflow."""
    if steps is None:
        steps = {
            "step-1": {
                "type": "logic",
                "id": "step-1",
                "code": "pass",
            }
        }
    return Workflow(start=start, steps=steps)


def create_manifest_v2(
    name: str = "Test Manifest",
    definitions: dict[str, Any] | None = None,
    workflow: Workflow | None = None,
    **kwargs: Any,
) -> ManifestV2:
    """Factory for ManifestV2."""
    if definitions is None:
        definitions = {}
    if workflow is None:
        workflow = create_workflow()

    defaults = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": name},
        "definitions": definitions,
        "workflow": workflow,
    }
    defaults.update(kwargs)
    return ManifestV2.model_validate(defaults)
