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

from coreason_manifest.builder import AgentBuilder
from coreason_manifest.spec.v2.definitions import ManifestV2


def simple_agent(
    name: str,
    prompt: str = "You are a helpful assistant.",
    model: str | None = None,
    tools: list[str] | None = None,
    knowledge: list[str] | None = None,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
) -> ManifestV2:
    """
    Create a simple agent manifest in a single function call.

    Args:
        name: The name of the agent (and ID).
        prompt: The system prompt/backstory.
        model: The LLM model to use.
        tools: List of tool IDs to enable.
        knowledge: List of knowledge sources.
        inputs: Dictionary defining input schema (optional).
                Can be a full JSON Schema object or a simple properties map.
        outputs: Dictionary defining output schema (optional).
                 Can be a full JSON Schema object or a simple properties map.

    Returns:
        A complete ManifestV2 object ready for serialization.
    """
    builder = AgentBuilder(name=name)
    builder.with_system_prompt(prompt)

    if model:
        builder.with_model(model)

    if tools:
        for tool in tools:
            builder.with_tool(tool)

    if knowledge:
        for k in knowledge:
            builder.with_knowledge(k)

    if inputs:
        if "type" in inputs and isinstance(inputs["type"], str):
            builder.interface_inputs = inputs
        else:
            builder.interface_inputs["properties"] = inputs

    if outputs:
        if "type" in outputs and isinstance(outputs["type"], str):
            builder.interface_outputs = outputs
        else:
            builder.interface_outputs["properties"] = outputs  # pragma: no cover

    return builder.build()
