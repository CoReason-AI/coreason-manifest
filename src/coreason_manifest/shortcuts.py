# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.common.capabilities import AgentCapabilities
from coreason_manifest.spec.v2.contracts import InterfaceDefinition
from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    ManifestMetadata,
    ManifestV2,
    Workflow,
)


def simple_agent(
    name: str,
    prompt: str | None = None,
    model: str | None = None,
    tools: list[str] | None = None,
    role: str = "Assistant",
    goal: str = "Help the user",
    version: str = "0.1.0",
) -> ManifestV2:
    """
    Create a simple single-agent ManifestV2 with sensible defaults.

    Args:
        name: Name of the agent (and the manifest).
        prompt: System prompt / backstory for the agent.
        model: LLM model ID (e.g., 'gpt-4').
        tools: List of tool IDs or URIs.
        role: The persona/job title (default: "Assistant").
        goal: Primary objective (default: "Help the user").
        version: Version of the manifest (default: "0.1.0").

    Returns:
        A valid ManifestV2 object ready for serialization.
    """
    # 1. Metadata
    metadata = ManifestMetadata(name=name, version=version)

    # 2. Interface (Default to generic object input/output)
    # This allows flexibility without strict schemas for simple agents.
    interface = InterfaceDefinition(
        inputs={"type": "object", "additionalProperties": True},
        outputs={"type": "object", "additionalProperties": True},
    )

    # 3. Agent Definition
    agent_def = AgentDefinition(
        id=name,
        name=name,
        role=role,
        goal=goal,
        backstory=prompt,
        model=model,
        tools=tools or [],
        capabilities=AgentCapabilities(),  # defaults
    )

    # 4. Workflow (Simple 1-step wrapper)
    workflow = Workflow(
        start="main",
        steps={
            "main": AgentStep(
                id="main",
                agent=name,
            )
        },
    )

    return ManifestV2(
        kind="Agent",
        metadata=metadata,
        interface=interface,
        definitions={name: agent_def},
        workflow=workflow,
    )
