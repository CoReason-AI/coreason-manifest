# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Literal

from pydantic import BaseModel

from coreason_manifest.spec.common.capabilities import (
    AgentCapabilities,
    CapabilityType,
    DeliveryMode,
)
from coreason_manifest.spec.v2.contracts import (
    InterfaceDefinition,
    PolicyDefinition,
    StateDefinition,
)
from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    GenericDefinition,
    ManifestMetadata,
    ManifestV2,
    Step,
    ToolDefinition,
    Workflow,
)

__all__ = ["AgentBuilder", "ManifestBuilder", "CapabilityType", "DeliveryMode", "TypedCapability"]


class TypedCapability[InputT: BaseModel, OutputT: BaseModel]:
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

    def build_definition(self) -> AgentDefinition:
        """
        Build the AgentDefinition object.
        """
        # Construct InterfaceDefinition
        interface = InterfaceDefinition(inputs=self.interface_inputs, outputs=self.interface_outputs)

        # Construct AgentCapabilities
        capabilities = AgentCapabilities(
            type=self._cap_type,
            delivery_mode=self._cap_delivery_mode,
        )

        # Construct AgentDefinition
        return AgentDefinition(
            id=self.name,
            name=self.name,
            role="Assistant",
            goal="Help the user",
            backstory=self.system_prompt,
            model=self.model,
            tools=self.tools,
            knowledge=self.knowledge,
            capabilities=capabilities,
            interface=interface,
        )

    def build(self) -> ManifestV2:
        """
        Build the final ManifestV2 object.

        Constructs the ManifestMetadata, InterfaceDefinition, AgentCapabilities,
        AgentDefinition, and a default Workflow.
        """
        # 1. Construct ManifestMetadata
        metadata = ManifestMetadata(name=self.name, version=self.version)

        # 2. Get Agent Definition
        agent_def = self.build_definition()

        # 3. Workflow
        workflow = Workflow(start="main", steps={"main": AgentStep(id="main", agent=self.name)})

        return ManifestV2(
            kind="Agent",
            metadata=metadata,
            interface=agent_def.interface,
            definitions={self.name: agent_def},
            workflow=workflow,
        )


class ManifestBuilder:
    """
    Builder for constructing complex ManifestV2 objects.

    Allows assembling multiple agents, tools, complex workflows, policies, and state
    definitions into a unified manifest.
    """

    def __init__(self, name: str, version: str = "0.1.0", kind: Literal["Recipe", "Agent"] = "Recipe"):
        self.name = name
        self.version = version
        self.kind = kind
        self.definitions: dict[str, ToolDefinition | AgentDefinition | GenericDefinition] = {}
        self.steps: dict[str, Step] = {}
        self.start_step_id: str | None = None
        self.interface = InterfaceDefinition()
        self.state = StateDefinition()
        self.policy = PolicyDefinition()
        self._metadata_extras: dict[str, Any] = {}

    def add_agent(self, agent: AgentDefinition) -> "ManifestBuilder":
        """Add an AgentDefinition to the manifest."""
        self.definitions[agent.id] = agent
        return self

    def add_tool(self, tool: ToolDefinition) -> "ManifestBuilder":
        """Add a ToolDefinition to the manifest."""
        self.definitions[tool.id] = tool
        return self

    def add_generic_definition(self, key: str, definition: GenericDefinition) -> "ManifestBuilder":
        """Add a generic definition to the manifest."""
        self.definitions[key] = definition
        return self

    def add_step(self, step: Step) -> "ManifestBuilder":
        """Add a workflow step."""
        self.steps[step.id] = step
        return self

    def set_start_step(self, step_id: str) -> "ManifestBuilder":
        """Set the ID of the starting step."""
        self.start_step_id = step_id
        return self

    def set_interface(self, interface: InterfaceDefinition) -> "ManifestBuilder":
        """Set the input/output interface for the manifest."""
        self.interface = interface
        return self

    def set_state(self, state: StateDefinition) -> "ManifestBuilder":
        """Set the state definition."""
        self.state = state
        return self

    def set_policy(self, policy: PolicyDefinition) -> "ManifestBuilder":
        """Set the policy definition."""
        self.policy = policy
        return self

    def set_metadata(self, key: str, value: Any) -> "ManifestBuilder":
        """Set extra metadata fields."""
        self._metadata_extras[key] = value
        return self

    def build(self) -> ManifestV2:
        """Build the final ManifestV2 object."""
        metadata = ManifestMetadata(name=self.name, version=self.version, **self._metadata_extras)

        if not self.start_step_id:
            if len(self.steps) == 1:
                self.start_step_id = next(iter(self.steps))
            else:
                raise ValueError("Start step must be specified for ManifestV2.")

        workflow = Workflow(start=self.start_step_id, steps=self.steps)

        return ManifestV2(
            apiVersion="coreason.ai/v2",
            kind=self.kind,
            metadata=metadata,
            interface=self.interface,
            state=self.state,
            policy=self.policy,
            definitions=self.definitions,
            workflow=workflow,
        )
