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

from coreason_manifest.spec.v2.definitions import AgentDefinition, InlineToolDefinition, ToolRequirement


def convert_to_openai_assistant(agent: AgentDefinition) -> dict[str, Any]:
    """
    Converts a Coreason Agent Definition into an OpenAI Assistant definition.

    Args:
        agent: The AgentDefinition to convert.

    Returns:
        A dictionary matching the OpenAI Assistant structure.
    """
    # 1. Instructions
    instructions_parts = [
        f"Role: {agent.role}",
        f"Goal: {agent.goal}",
    ]
    if agent.backstory:
        instructions_parts.append(f"Backstory: {agent.backstory}")

    instructions = "\n\n".join(instructions_parts)

    # 2. Tools
    openai_tools = []

    # Process tools
    for tool in agent.tools:
        if isinstance(tool, InlineToolDefinition):
            # Map InlineToolDefinition to OpenAI function tool
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
        elif isinstance(tool, ToolRequirement):
            # For remote tools, we can't fully define them without schema retrieval.
            # We skip them for now.
            pass

    # 3. Model
    # Default to a modern model if not specified
    model = agent.model if agent.model else "gpt-4o"

    return {
        "name": agent.name,
        "instructions": instructions,
        "tools": openai_tools,
        "model": model,
        "metadata": {
            "source": "coreason-manifest",
            "agent_id": agent.id,
            "version": "v2",
        },
    }
