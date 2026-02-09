# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Generator

from coreason_manifest.spec.v2.definitions import AgentDefinition, InlineToolDefinition


class BaseManifestAdapter:
    """Base class for adapting Coreason Agents to external frameworks."""

    @staticmethod
    def _build_system_prompt(agent: AgentDefinition, include_header: bool = False) -> str:
        """
        Constructs a standard system prompt from agent attributes.

        Args:
            agent: The agent definition.
            include_header: If True, prepends "You are {agent.name}."
        """
        parts = []
        if include_header:
            parts.append(f"You are {agent.name}.")

        parts.extend([
            f"Role: {agent.role}",
            f"Goal: {agent.goal}",
        ])

        if agent.backstory:
            parts.append(f"Backstory: {agent.backstory}")

        return "\n\n".join(parts)

    @staticmethod
    def _iter_inline_tools(agent: AgentDefinition) -> Generator[InlineToolDefinition, None, None]:
        """Yields only InlineToolDefinitions, skipping ToolRequirements (remote tools)."""
        for tool in agent.tools:
            if isinstance(tool, InlineToolDefinition):
                yield tool
