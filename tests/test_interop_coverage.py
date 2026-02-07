# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.definitions import AgentDefinition
from coreason_manifest.utils.langchain_adapter import convert_to_langchain_kwargs
from coreason_manifest.utils.openai_adapter import convert_to_openai_assistant


def test_openai_conversion_with_backstory() -> None:
    """Test conversion to OpenAI format including backstory."""
    agent = AgentDefinition(
        id="story-agent",
        name="Story Agent",
        role="Teller",
        goal="Tell stories",
        backstory="Once upon a time...",
    )

    result = convert_to_openai_assistant(agent)

    assert "Backstory: Once upon a time..." in result["instructions"]


def test_langchain_conversion_with_backstory() -> None:
    """Test conversion to LangChain format including backstory."""
    agent = AgentDefinition(
        id="story-agent-lc",
        name="Story Agent LC",
        role="Teller",
        goal="Tell stories",
        backstory="In a galaxy far, far away...",
    )

    result = convert_to_langchain_kwargs(agent)

    assert "Backstory: In a galaxy far, far away..." in result["system_message"]
