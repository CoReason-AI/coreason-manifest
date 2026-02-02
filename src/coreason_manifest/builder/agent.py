# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import hashlib
from datetime import datetime, timezone
from typing import Optional, Self
from uuid import uuid4

from coreason_manifest.builder.capability import TypedCapability
from coreason_manifest.definitions.agent import (
    AgentDefinition,
    AgentDependencies,
    AgentMetadata,
    AgentRuntimeConfig,
    ModelConfig,
)


class AgentBuilder:
    """A fluent builder for constructing valid AgentDefinition objects.

    This builder simplifies the creation of Agent manifests by allowing developers
    to use Python objects and methods instead of constructing raw dictionaries and
    schema structures manually.
    """

    def __init__(
        self,
        name: str,
        version: str = "0.1.0",
        author: str = "Unknown",
    ) -> None:
        """Initialize the AgentBuilder.

        Args:
            name: Name of the Agent.
            version: Semantic Version of the Agent.
            author: Author of the Agent.
        """
        self.name = name
        self.version = version
        self.author = author

        self._capabilities: list[TypedCapability] = []
        self._system_prompt: Optional[str] = None
        self._model_name: str = "gpt-4o"  # Default model
        self._temperature: float = 0.0

    def with_capability(self, cap: TypedCapability) -> Self:
        """Add a typed capability to the agent.

        Args:
            cap: The TypedCapability instance to add.

        Returns:
            The builder instance (for chaining).
        """
        self._capabilities.append(cap)
        return self

    def with_system_prompt(self, prompt: str) -> Self:
        """Set the global system prompt for the agent.

        Args:
            prompt: The system prompt text.

        Returns:
            The builder instance (for chaining).
        """
        self._system_prompt = prompt
        return self

    def with_model(self, model: str, temperature: float = 0.0) -> Self:
        """Configure the LLM model for the agent.

        Args:
            model: The model identifier (e.g., 'gpt-4').
            temperature: Generation temperature.

        Returns:
            The builder instance (for chaining).
        """
        self._model_name = model
        self._temperature = temperature
        return self

    def build(self) -> AgentDefinition:
        """Construct the final immutable AgentDefinition.

        Compiles all typed capabilities into schemas and assembles the full manifest.

        Returns:
            A validated AgentDefinition object.
        """
        # Generate dummy integrity hash based on name as per instructions
        integrity_hash = hashlib.sha256(self.name.encode("utf-8")).hexdigest()

        metadata = AgentMetadata(
            id=uuid4(),
            version=self.version,
            name=self.name,
            author=self.author,
            created_at=datetime.now(timezone.utc),
            requires_auth=False,
        )

        model_config = ModelConfig(
            model=self._model_name,
            temperature=self._temperature,
            system_prompt=self._system_prompt,
        )

        # Atomic Agent configuration (no nodes/edges)
        config = AgentRuntimeConfig(
            nodes=[],
            edges=[],
            entry_point=None,
            model_config=model_config,
            system_prompt=self._system_prompt,
        )

        return AgentDefinition(
            metadata=metadata,
            capabilities=[cap.to_definition() for cap in self._capabilities],
            config=config,
            dependencies=AgentDependencies(),
            integrity_hash=integrity_hash,
        )
