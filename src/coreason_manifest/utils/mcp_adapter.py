# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import re
from typing import Any

from coreason_manifest.spec.v2.definitions import AgentDefinition


def create_mcp_tool_definition(agent: AgentDefinition) -> dict[str, Any]:
    """
    Converts a Coreason Agent Definition into an MCP Tool structure.

    This function adapts the agent's identity and interface to match the Model Context Protocol (MCP)
    'Tool' specification.

    WARNING: This conversion is lossy and opinionated:
    1. Name Sanitization: The agent name is lowercased and non-alphanumeric characters are replaced
       with underscores to meet MCP strict naming conventions.
    2. Description Fallback: Uses `backstory` if available, otherwise `goal`, otherwise a generic string.
    3. Schema: Directly uses `agent.interface.inputs` as `inputSchema`. Ensure this is a valid JSON Schema.

    Args:
        agent (AgentDefinition): The source agent definition.

    Returns:
        dict[str, Any]: A dictionary compatible with MCP's 'Tool' type.
    """
    # Sanitize name: lowercase, replace non-alphanumeric with _, collapse _, strip _
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", agent.name).lower()
    name = re.sub(r"_+", "_", name).strip("_")

    # Description: use backstory or goal or generic fallback
    description = agent.backstory or agent.goal or f"Agent {agent.name}"

    # Input Schema: use agent.interface.inputs
    # We assume agent.interface.inputs is a valid JSON Schema object.
    input_schema = agent.interface.inputs

    return {"name": name, "description": description, "inputSchema": input_schema}
