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


def convert_to_langchain_kwargs(agent: AgentDefinition) -> dict[str, Any]:
    """
    Convert a Coreason AgentDefinition into LangChain initialization arguments.

    This function extracts the system message (prompt) and tool schemas in a format
    compatible with LangChain's agent initialization (e.g., for `create_openai_tools_agent`
    or `bind_tools`).

    Args:
        agent: The agent definition to convert.

    Returns:
        A dictionary containing:
        - `system_message`: A string containing the combined role, goal, and backstory.
        - `tool_schemas`: A list of dictionaries representing the tool schemas (compatible with OpenAI function format).
        - `model_name`: The name of the LLM model to use.
    """
    # Construct the system message
    instructions_parts = [
        f"You are {agent.name}.",
        f"Role: {agent.role}",
        f"Goal: {agent.goal}",
    ]
    if agent.backstory:
        instructions_parts.append(f"Backstory: {agent.backstory}")

    system_message = "\n\n".join(instructions_parts)

    # Convert tools to schemas compatible with LangChain's bind_tools (which accepts OpenAI format)
    tool_schemas = []
    for tool in agent.tools:
        if isinstance(tool, InlineToolDefinition):
            tool_schemas.append(
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
            # Remote tools are skipped as their schema is not available locally.
            continue

    return {
        "system_message": system_message,
        "tool_schemas": tool_schemas,
        "model_name": agent.model or "gpt-4",  # Default to gpt-4 if not specified
    }
