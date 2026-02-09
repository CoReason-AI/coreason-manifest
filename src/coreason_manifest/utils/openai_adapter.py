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

from coreason_manifest.spec.v2.definitions import AgentDefinition
from coreason_manifest.utils.base_adapter import BaseManifestAdapter


def convert_to_openai_assistant(agent: AgentDefinition) -> dict[str, Any]:
    """
    Convert a Coreason AgentDefinition into an OpenAI Assistant configuration.

    This function maps the agent's identity, instructions, and tools to the format
    expected by the OpenAI Assistants API.

    WARNING: This conversion involves lossy transformations:
    1. Instructions: Concatenates `role`, `goal`, and `backstory` into a single text block.
    2. Tool Dropping: SILENTLY DROPS any `ToolRequirement` (remote tools) because their
       schema is not available locally for registration with OpenAI.
    3. Model Default: Invents "gpt-4-turbo-preview" as the default model if `agent.model`
       is not specified.

    Args:
        agent (AgentDefinition): The agent definition to convert.

    Returns:
        dict[str, Any]: A dictionary representing the OpenAI Assistant configuration.
    """
    instructions = BaseManifestAdapter._build_system_prompt(agent, include_header=False)

    tools = []
    for tool in BaseManifestAdapter._iter_inline_tools(agent):
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
