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
    Convert a Coreason AgentDefinition into an OpenAI Assistant configuration.

    This function maps the agent's identity, instructions, and tools to the format
    expected by the OpenAI Assistants API.

    Args:
        agent: The agent definition to convert.

    Returns:
        A dictionary representing the OpenAI Assistant configuration.
    """
    instructions_parts = [
        f"Role: {agent.role}",
        f"Goal: {agent.goal}",
    ]
    if agent.backstory:
        instructions_parts.append(f"Backstory: {agent.backstory}")

    instructions = "\n\n".join(instructions_parts)

    tools = []
    for tool in agent.tools:
        if isinstance(tool, InlineToolDefinition):
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
            )
        elif isinstance(tool, ToolRequirement):
            # Remote tools (ToolRequirement) are skipped as their schema is not available locally.
            continue

    return {
        "name": agent.name,
        "instructions": instructions,
        "tools": tools,
        "model": agent.model or "gpt-4-turbo-preview",  # Default model if not specified
        "metadata": {
            "coreason_agent_id": agent.id,
            "coreason_agent_role": agent.role,
        },
    }
