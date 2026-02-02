# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

from coreason_manifest.definitions.agent import AgentCapability, CapabilityType

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class TypedCapability(Generic[InputT, OutputT]):
    """A build-time capability wrapper that uses Pydantic models for I/O definitions.

    This class allows developers to define capabilities using strong types (Pydantic models),
    which are then compiled down to the required JSON Schema format for the Agent Manifest.
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_model: type[InputT],
        output_model: type[OutputT],
        type: CapabilityType = CapabilityType.ATOMIC,
        injected_params: Optional[list[str]] = None,
    ) -> None:
        """Initialize a TypedCapability.

        Args:
            name: Unique name for this capability.
            description: What this mode does.
            input_model: The Pydantic model defining the input structure.
            output_model: The Pydantic model defining the output structure.
            type: Interaction mode (default: ATOMIC).
            injected_params: List of parameters injected by the system (optional).
        """
        self.name = name
        self.description = description
        self.input_model = input_model
        self.output_model = output_model
        self.type = type
        self.injected_params = injected_params or []

    def to_definition(self) -> AgentCapability:
        """Compile the typed capability into a strict AgentCapability definition.

        Returns:
            An instance of AgentCapability with inputs/outputs converted to JSON Schema.
        """
        return AgentCapability(
            name=self.name,
            type=self.type,
            description=self.description,
            inputs=self.input_model.model_json_schema(),
            outputs=self.output_model.model_json_schema(),
            injected_params=self.injected_params,
        )
