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
from coreason_manifest.spec.v2.contracts import InterfaceDefinition
from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    ManifestMetadata,
    ManifestV2,
    Workflow,
)

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class TypedCapability(Generic[InputT, OutputT]):
    """
    A strictly typed capability definition that wraps Pydantic models.

    This class handles the generation of JSON Schema for the input and output
    contracts of an agent capability.
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_model: type[InputT],
        output_model: type[OutputT],
        type: CapabilityType = CapabilityType.GRAPH,
        delivery_mode: DeliveryMode = DeliveryMode.REQUEST_RESPONSE,
    ):
        self.name = name
        self.description = description
        self.input_model = input_model
        self.output_model = output_model
        self.type = type
        self.delivery_mode = delivery_mode

    def get_input_schema(self) -> dict[str, Any]:
        """Generate the JSON Schema for the input model."""
        return self.input_model.model_json_schema()

    def get_output_schema(self) -> dict[str, Any]:
        """Generate the JSON Schema for the output model."""
        return self.output_model.model_json_schema()


class AgentBuilder:
    """
    Fluent builder for constructing AgentDefinition and ManifestV2 objects.

    Provides a clean API for defining agents, capabilities, tools, and knowledge,
    abstracting away the complexity of the underlying Pydantic models.
    """

    def __init__(self, name: str, version: str = "0.1.0"):
        self.name = name
        self.version = version
        self.tools: list[str] = []
        self.knowledge: list[str] = []
        self.system_prompt: str | None = None
        self.model: str | None = None

        # Internal state for capabilities
        self.interface_inputs: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
        self.interface_outputs: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

        # Capability flags defaults
        self._cap_type = CapabilityType.GRAPH
        self._cap_delivery_mode = DeliveryMode.REQUEST_RESPONSE

    def with_system_prompt(self, prompt: str) -> "AgentBuilder":
        """Set the system prompt (backstory) for the agent."""
        self.system_prompt = prompt
        return self

    def with_model(self, model: str) -> "AgentBuilder":
        """Set the LLM model ID."""
        self.model = model
        return self

    def with_tool(self, tool_id: str) -> "AgentBuilder":
        """Add a tool ID to the agent's toolset."""
        self.tools.append(tool_id)
        return self

    def with_knowledge(self, uri: str) -> "AgentBuilder":
        """Add a knowledge source URI."""
        self.knowledge.append(uri)
        return self

    def with_capability(self, cap: TypedCapability[Any, Any]) -> "AgentBuilder":
        """
        Add a capability to the agent.

        Merges the capability's input/output schemas into the agent's interface
        and updates capability flags (e.g., delivery mode).
        """
        # Merge input schema
        cap_input = cap.get_input_schema()
        self._merge_schema(self.interface_inputs, cap_input)

        # Merge output schema
        cap_output = cap.get_output_schema()
        self._merge_schema(self.interface_outputs, cap_output)

        # Update capability settings
        if cap.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS:
            self._cap_delivery_mode = DeliveryMode.SERVER_SENT_EVENTS

        self._cap_type = cap.type

        return self

    def _merge_schema(self, target: dict[str, Any], source: dict[str, Any]) -> None:
        """Helper to merge JSON Schemas (properties, required, $defs)."""
        if "properties" in source:
            target.setdefault("properties", {}).update(source["properties"])

        if "required" in source:
            current_req = set(target.get("required", []))
            current_req.update(source["required"])
            target["required"] = list(current_req)

        if "$defs" in source:
            target.setdefault("$defs", {}).update(source["$defs"])

    def build(self) -> ManifestV2:
        """
        Build the final ManifestV2 object.

        Constructs the ManifestMetadata, InterfaceDefinition, AgentCapabilities,
        AgentDefinition, and a default Workflow.
        """
        # 1. Construct ManifestMetadata
        metadata = ManifestMetadata(name=self.name, version=self.version)

        # 2. Construct InterfaceDefinition
        interface = InterfaceDefinition(inputs=self.interface_inputs, outputs=self.interface_outputs)

        # 3. Construct AgentCapabilities
        capabilities = AgentCapabilities(
            type=self._cap_type,
            delivery_mode=self._cap_delivery_mode,
        )

        # 4. Construct AgentDefinition
        agent_def = AgentDefinition(
            id=self.name,
            name=self.name,
            role="Assistant",
            goal="Help the user",
            backstory=self.system_prompt,
            model=self.model,
            tools=self.tools,
            knowledge=self.knowledge,
            capabilities=capabilities,
        )

        # 5. Workflow
        workflow = Workflow(start="main", steps={"main": AgentStep(id="main", agent=self.name)})

        return ManifestV2(
            kind="Agent",
            metadata=metadata,
            interface=interface,
            definitions={self.name: agent_def},
            workflow=workflow,
        )
