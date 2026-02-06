# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from coreason_manifest.spec.common.capabilities import (
    AgentCapabilities,
    CapabilityType,
    DeliveryMode,
)
from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    InterfaceDefinition,
    ManifestMetadata,
    ManifestV2,
    Workflow,
)

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)


class TypedCapability(Generic[TInput, TOutput]):
    """A strongly-typed capability definition."""

    def __init__(
        self,
        name: str,
        description: str,
        input_model: type[TInput],
        output_model: type[TOutput],
        type: CapabilityType = CapabilityType.GRAPH,
        delivery_mode: DeliveryMode = DeliveryMode.REQUEST_RESPONSE,
    ):
        self.name = name
        self.description = description
        self.input_model = input_model
        self.output_model = output_model
        self.type = type
        self.delivery_mode = delivery_mode

    def to_interface(self) -> dict[str, dict[str, Any]]:
        """Generate JSON Schema for inputs and outputs."""
        return {
            "inputs": self.input_model.model_json_schema(),
            "outputs": self.output_model.model_json_schema(),
        }


class AgentBuilder:
    """Builder for defining Agents with a fluent interface."""

    def __init__(self, name: str, version: str = "0.1.0", description: str | None = None):
        self._name = name
        self._version = version
        self._description = description
        self._system_prompt: str | None = None
        self._model: str | None = None
        self._tools: list[str] = []
        self._capabilities: list[TypedCapability[Any, Any]] = []

        # Defaults for required AgentDefinition fields
        self._role: str = "General Assistant"
        self._goal: str = "Help the user"

    def with_system_prompt(self, prompt: str) -> "AgentBuilder":
        self._system_prompt = prompt
        return self

    def with_model(self, model: str) -> "AgentBuilder":
        self._model = model
        return self

    def with_tool(self, tool_id: str) -> "AgentBuilder":
        self._tools.append(tool_id)
        return self

    def with_capability(self, cap: TypedCapability[Any, Any]) -> "AgentBuilder":
        self._capabilities.append(cap)
        return self

    def with_role(self, role: str) -> "AgentBuilder":
        self._role = role
        return self

    def with_goal(self, goal: str) -> "AgentBuilder":
        self._goal = goal
        return self

    def build(self) -> ManifestV2:
        """Build the Agent Manifest."""
        # 1. Construct ManifestMetadata
        metadata = ManifestMetadata(
            name=self._name,
        )

        # 2. Construct InterfaceDefinition
        # Merge schemas from capabilities
        input_schema: dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        output_schema: dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        for cap in self._capabilities:
            iface = cap.to_interface()
            # Merge inputs
            cap_input = iface["inputs"]
            if "properties" in cap_input:
                input_schema["properties"].update(cap_input["properties"])
            if "required" in cap_input:
                # Merge required lists, avoid duplicates
                current_required = set(input_schema.get("required", []))
                current_required.update(cap_input.get("required", []))
                input_schema["required"] = list(current_required)

            # Merge outputs
            cap_output = iface["outputs"]
            if "properties" in cap_output:
                output_schema["properties"].update(cap_output["properties"])
            if "required" in cap_output:
                current_required_out = set(output_schema.get("required", []))
                current_required_out.update(cap_output.get("required", []))
                output_schema["required"] = list(current_required_out)

        # 3. Construct AgentCapabilities
        # Determine flags based on added capabilities.
        # If any capability requires SSE, we set SSE.
        delivery_mode = DeliveryMode.REQUEST_RESPONSE
        for cap in self._capabilities:
            if cap.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS:
                delivery_mode = DeliveryMode.SERVER_SENT_EVENTS
                break

        agent_caps = AgentCapabilities(delivery_mode=delivery_mode)

        # 4. Construct AgentDefinition
        agent_def = AgentDefinition(
            id=self._name,  # Using name as ID for simplicity
            name=self._name,
            role=self._role,
            goal=self._goal,
            backstory=self._system_prompt,
            model=self._model,
            tools=self._tools,
            capabilities=agent_caps,
        )

        # 5. Construct Workflow
        # Simple default workflow
        workflow = Workflow(start="main", steps={"main": AgentStep(id="main", agent=self._name)})

        return ManifestV2(
            kind="Agent",
            metadata=metadata,
            interface=InterfaceDefinition(inputs=input_schema, outputs=output_schema),
            definitions={self._name: agent_def},
            workflow=workflow,
        )
