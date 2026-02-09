# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Literal, Self

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
    InlineToolDefinition,
    ManifestMetadata,
    ManifestV2,
    Step,
    ToolDefinition,
    ToolRequirement,
    Workflow,
)

__all__ = ["AgentBuilder", "CapabilityType", "DeliveryMode", "ManifestBuilder", "TypedCapability"]


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
        capability_type: CapabilityType = CapabilityType.GRAPH,
        delivery_mode: DeliveryMode = DeliveryMode.REQUEST_RESPONSE,
    ):
        self.name = name
        self.description = description
        self.input_model = input_model
        self.output_model = output_model
        self.type = capability_type
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
        self.tools: list[ToolRequirement | InlineToolDefinition] = []
        self.knowledge: list[str] = []
        self.system_prompt: str | None = None
        self.model: str | None = None

        # Internal state for capabilities
        self.interface_inputs: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
        self.interface_outputs: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

        # Capability flags defaults
        self._cap_type = CapabilityType.GRAPH
        self._cap_delivery_mode = DeliveryMode.REQUEST_RESPONSE

    def with_system_prompt(self, prompt: str) -> Self:
        """
        Set the system prompt (backstory) for the agent.

        Args:
            prompt (str): The system prompt text.

        Returns:
            Self: The builder instance for chaining.
        """
        self.system_prompt = prompt
        return self

    def with_model(self, model: str) -> Self:
        """
        Set the LLM model ID.

        Args:
            model (str): The model identifier.

        Returns:
            Self: The builder instance for chaining.
        """
        self.model = model
        return self

    def with_tool(self, tool_id: str) -> Self:
        """
        Add a tool ID to the agent's toolset.

        Args:
            tool_id (str): The identifier of the tool.

        Returns:
            Self: The builder instance for chaining.
        """
        self.tools.append(ToolRequirement(uri=tool_id))
        return self

    def with_knowledge(self, uri: str) -> Self:
        """
        Add a knowledge source URI.

        Args:
            uri (str): The URI of the knowledge source.

        Returns:
            Self: The builder instance for chaining.
        """
        self.knowledge.append(uri)
        return self

    def with_capability(self, cap: TypedCapability[Any, Any]) -> Self:
        """
        Add a capability to the agent.

        Merges the capability's input/output schemas into the agent's interface
        and updates capability flags (e.g., delivery mode).

        Args:
            cap (TypedCapability): The typed capability definition.

        Returns:
            Self: The builder instance for chaining.
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

        Returns:
            AgentDefinition: The constructed agent definition.
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

        Returns:
            ManifestV2: The fully constructed manifest.
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

    def add_agent(self, agent: AgentDefinition) -> Self:
        """
        Add an AgentDefinition to the manifest.

        Args:
            agent (AgentDefinition): The agent definition to add.

        Returns:
            Self: The builder instance for chaining.
        """
        self.definitions[agent.id] = agent
        return self

    def add_tool(self, tool: ToolDefinition) -> Self:
        """
        Add a ToolDefinition to the manifest.

        Args:
            tool (ToolDefinition): The tool definition to add.

        Returns:
            Self: The builder instance for chaining.
        """
        self.definitions[tool.id] = tool
        return self

    def add_generic_definition(self, key: str, definition: GenericDefinition) -> Self:
        """
        Add a generic definition to the manifest.

        Args:
            key (str): The key/id for the definition.
            definition (GenericDefinition): The definition object.

        Returns:
            Self: The builder instance for chaining.
        """
        self.definitions[key] = definition
        return self

    def add_step(self, step: Step) -> Self:
        """
        Add a workflow step.

        Args:
            step (Step): The workflow step to add.

        Returns:
            Self: The builder instance for chaining.
        """
        self.steps[step.id] = step
        return self

    def set_start_step(self, step_id: str) -> Self:
        """
        Set the ID of the starting step.

        Args:
            step_id (str): The ID of the start step.

        Returns:
            Self: The builder instance for chaining.
        """
        self.start_step_id = step_id
        return self

    def set_interface(self, interface: InterfaceDefinition) -> Self:
        """
        Set the input/output interface for the manifest.

        Args:
            interface (InterfaceDefinition): The interface definition.

        Returns:
            Self: The builder instance for chaining.
        """
        self.interface = interface
        return self

    def set_state(self, state: StateDefinition) -> Self:
        """
        Set the state definition.

        Args:
            state (StateDefinition): The state definition.

        Returns:
            Self: The builder instance for chaining.
        """
        self.state = state
        return self

    def set_policy(self, policy: PolicyDefinition) -> Self:
        """
        Set the policy definition.

        Args:
            policy (PolicyDefinition): The policy definition.

        Returns:
            Self: The builder instance for chaining.
        """
        self.policy = policy
        return self

    def set_metadata(self, key: str, value: Any) -> Self:
        """
        Set extra metadata fields.

        Args:
            key (str): The metadata key.
            value (Any): The metadata value.

        Returns:
            Self: The builder instance for chaining.
        """
        self._metadata_extras[key] = value
        return self

    def build(self) -> ManifestV2:
        """
        Build the final ManifestV2 object.

        Returns:
            ManifestV2: The fully constructed manifest.

        Raises:
            ValueError: If the start step is not specified and cannot be inferred.
        """
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
