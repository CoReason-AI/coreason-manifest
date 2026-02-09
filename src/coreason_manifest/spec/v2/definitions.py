# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Annotated, Any, Literal, Self

from pydantic import ConfigDict, Field, field_validator, model_validator

from coreason_manifest.spec.common.capabilities import AgentCapabilities
from coreason_manifest.spec.common.interoperability import AgentRuntimeConfig
from coreason_manifest.spec.common_base import CoReasonBaseModel, StrictUri, ToolRiskLevel
from coreason_manifest.spec.v2.contracts import InterfaceDefinition, PolicyDefinition, StateDefinition
from coreason_manifest.spec.v2.evaluation import EvaluationProfile
from coreason_manifest.spec.v2.packs import MCPResourceDefinition, ToolPackDefinition
from coreason_manifest.spec.v2.provenance import ProvenanceData
from coreason_manifest.spec.v2.resources import ModelProfile
from coreason_manifest.spec.v2.skills import SkillDefinition

__all__ = [
    "AgentDefinition",
    "AgentStep",
    "BaseStep",
    "CouncilStep",
    "DesignMetadata",
    "GenericDefinition",
    "InlineToolDefinition",
    "InterfaceDefinition",
    "LogicStep",
    "ManifestMetadata",
    "ManifestV2",
    "SkillDefinition",
    "Step",
    "SwitchStep",
    "ToolDefinition",
    "ToolRequirement",
    "Workflow",
]


class DesignMetadata(CoReasonBaseModel):
    """
    UI-specific metadata for the visual builder.

    Attributes:
        x (float): X coordinate on the canvas.
        y (float): Y coordinate on the canvas.
        icon (str | None): Icon name or URL.
        color (str | None): Color code (hex/name).
        label (str | None): Display label.
        zoom (float | None): Zoom level.
        collapsed (bool): Whether the node is collapsed in UI. (Default: False).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    x: float = Field(..., description="X coordinate on the canvas.")
    y: float = Field(..., description="Y coordinate on the canvas.")
    icon: str | None = Field(None, description="Icon name or URL.")
    color: str | None = Field(None, description="Color code (hex/name).")
    label: str | None = Field(None, description="Display label.")
    zoom: float | None = Field(None, description="Zoom level.")
    collapsed: bool = Field(False, description="Whether the node is collapsed in UI.")


class ToolDefinition(CoReasonBaseModel):
    """
    Definition of an external tool.

    Attributes:
        type (Literal["tool"]): Discriminator. (Default: "tool").
        id (str): Unique ID for the tool within the manifest.
        name (str): Name of the tool.
        uri (StrictUri): The MCP endpoint URI.
        risk_level (ToolRiskLevel): Risk level (safe, standard, critical).
        description (str | None): Description of the tool.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["tool"] = "tool"
    id: str = Field(..., description="Unique ID for the tool within the manifest.")
    name: str = Field(..., description="Name of the tool.")
    uri: StrictUri = Field(..., description="The MCP endpoint URI.")
    risk_level: ToolRiskLevel = Field(..., description="Risk level (safe, standard, critical).")
    description: str | None = Field(None, description="Description of the tool.")


class ToolRequirement(CoReasonBaseModel):
    """
    A requirement for a remote tool.

    Attributes:
        type (Literal["remote"]): Discriminator. (Default: "remote").
        uri (str): The URI of the tool or reference ID.
        hash (str | None): Optional integrity hash.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["remote"] = "remote"
    uri: str = Field(..., description="The URI of the tool or reference ID.")
    hash: str | None = Field(None, description="Optional integrity hash.")


class InlineToolDefinition(CoReasonBaseModel):
    """
    A tool defined directly within the manifest (Serverless/Local).

    Attributes:
        type (Literal["inline"]): Discriminator. (Default: "inline").
        name (str): Name of the tool. (Pattern: ^[a-zA-Z0-9_-]+$).
        description (str): Description of what the tool does.
        parameters (dict[str, Any]): JSON Schema for arguments. (Validation: Must be type='object').
        code_hash (str | None): Optional integrity check for implementation code.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["inline"] = "inline"
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", description="Name of the tool.")
    description: str = Field(..., description="Description of what the tool does.")
    parameters: dict[str, Any] = Field(..., description="JSON Schema for arguments.")
    code_hash: str | None = Field(None, description="Optional integrity check for implementation code.")

    @field_validator("parameters")
    @classmethod
    def validate_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        if v.get("type") != "object":
            raise ValueError("Tool parameters must be a JSON Schema object.")
        return v


class AgentDefinition(CoReasonBaseModel):
    """
    Definition of an Agent.

    Attributes:
        type (Literal["agent"]): Discriminator. (Default: "agent").
        id (str): Unique ID for the agent.
        name (str): Name of the agent.
        role (str): The persona/job title.
        goal (str): Primary objective.
        backstory (str | None): Backstory or directives.
        model (str | None): LLM identifier.
        tools (list[ToolRequirement | InlineToolDefinition]): List of Tool Requirements or Inline Definitions.
            (Validation: Normalizes string URIs or partial dicts to ToolRequirement).
        knowledge (list[str]): List of file paths or knowledge base IDs.
        skills (list[str]): List of Skill IDs to equip this agent with.
        context_strategy (Literal["full", "compressed", "hybrid"]): Context optimization strategy for skills.
            (Default: "hybrid").
        interface (InterfaceDefinition): Input/Output contract.
        capabilities (AgentCapabilities): Feature flags and capabilities for the agent.
        runtime (AgentRuntimeConfig | None): Configuration for the agent runtime environment
            (e.g. environment variables).
        evaluation (EvaluationProfile | None): Quality assurance and testing metadata.
        resources (ModelProfile | None): Hardware, pricing, and operational constraints for this agent.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["agent"] = "agent"
    id: str = Field(..., description="Unique ID for the agent.")
    name: str = Field(..., description="Name of the agent.")
    role: str = Field(..., description="The persona/job title.")
    goal: str = Field(..., description="Primary objective.")
    backstory: str | None = Field(None, description="Backstory or directives.")
    model: str | None = Field(None, description="LLM identifier.")
    tools: list[Annotated[ToolRequirement | InlineToolDefinition, Field(discriminator="type")]] = Field(
        default_factory=list, description="List of Tool Requirements or Inline Definitions."
    )
    knowledge: list[str] = Field(default_factory=list, description="List of file paths or knowledge base IDs.")
    skills: list[str] = Field(default_factory=list, description="List of Skill IDs to equip this agent with.")
    context_strategy: Literal["full", "compressed", "hybrid"] = Field(
        "hybrid", description="Context optimization strategy for skills."
    )

    interface: InterfaceDefinition = Field(default_factory=InterfaceDefinition, description="Input/Output contract.")
    capabilities: AgentCapabilities = Field(
        default_factory=AgentCapabilities, description="Feature flags and capabilities for the agent."
    )
    runtime: AgentRuntimeConfig | None = Field(
        None, description="Configuration for the agent runtime environment (e.g. environment variables)."
    )
    evaluation: EvaluationProfile | None = Field(None, description="Quality assurance and testing metadata.")
    resources: ModelProfile | None = Field(
        None, description="Hardware, pricing, and operational constraints for this agent."
    )


class GenericDefinition(CoReasonBaseModel):
    """
    Fallback for unknown definitions.

    Allows any extra fields.
    """

    model_config = ConfigDict(extra="allow", frozen=True)


class BaseStep(CoReasonBaseModel):
    """
    Base attributes for all steps.

    Attributes:
        id (str): Unique identifier for the step.
        inputs (dict[str, Any]): Input arguments for the step.
        design_metadata (DesignMetadata | None): UI metadata. (Alias: 'x-design').
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    id: str = Field(..., description="Unique identifier for the step.")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input arguments for the step.")
    design_metadata: DesignMetadata | None = Field(None, description="UI metadata.")


class AgentStep(BaseStep):
    """
    A step that executes an AI Agent.

    Attributes:
        type (Literal["agent"]): Discriminator. (Default: "agent").
        agent (str): Reference to an Agent definition (by ID or name).
        next (str | None): ID of the next step to execute.
        system_prompt (str | None): Optional override for system prompt.
        temporary_skills (list[str]): Skills injected into the agent ONLY for this specific step.
    """

    type: Literal["agent"] = "agent"
    agent: str = Field(..., description="Reference to an Agent definition (by ID or name).")
    next: str | None = Field(None, description="ID of the next step to execute.")
    system_prompt: str | None = Field(None, description="Optional override for system prompt.")
    temporary_skills: list[str] = Field(
        default_factory=list, description="Skills injected into the agent ONLY for this specific step."
    )


class LogicStep(BaseStep):
    """
    A step that executes custom logic.

    Attributes:
        type (Literal["logic"]): Discriminator. (Default: "logic").
        code (str): Python code or reference to logic to execute.
        next (str | None): ID of the next step to execute.
    """

    type: Literal["logic"] = "logic"
    code: str = Field(..., description="Python code or reference to logic to execute.")
    next: str | None = Field(None, description="ID of the next step to execute.")


class CouncilStep(BaseStep):
    """
    A step that involves multiple voters/agents.

    Attributes:
        type (Literal["council"]): Discriminator. (Default: "council").
        voters (list[str]): List of voters (Agent IDs).
        strategy (str): Voting strategy (e.g., consensus, majority). (Default: "consensus").
        next (str | None): ID of the next step to execute.
    """

    type: Literal["council"] = "council"
    voters: list[str] = Field(..., description="List of voters (Agent IDs).")
    strategy: str = Field("consensus", description="Voting strategy (e.g., consensus, majority).")
    next: str | None = Field(None, description="ID of the next step to execute.")


class SwitchStep(BaseStep):
    """
    A step that routes execution based on conditions.

    Attributes:
        type (Literal["switch"]): Discriminator. (Default: "switch").
        cases (dict[str, str]): Dictionary of condition expressions to Step IDs.
        default (str | None): Default Step ID if no cases match.
    """

    type: Literal["switch"] = "switch"
    cases: dict[str, str] = Field(..., description="Dictionary of condition expressions to Step IDs.")
    default: str | None = Field(None, description="Default Step ID if no cases match.")
    # Note: 'next' is deliberately excluded for SwitchStep in favor of cases/default.

    @field_validator("cases")
    @classmethod
    def validate_cases(cls, v: dict[str, str]) -> dict[str, str]:
        for condition in v.keys():
            if not condition.strip():
                raise ValueError("Switch condition cannot be empty.")
        return v


Step = Annotated[
    AgentStep | LogicStep | CouncilStep | SwitchStep,
    Field(discriminator="type", description="Polymorphic step definition."),
]


class Workflow(CoReasonBaseModel):
    """
    Defines the execution topology.

    Attributes:
        start (str): ID of the starting step.
        steps (dict[str, Step]): Dictionary of all steps indexed by ID.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    start: str = Field(..., description="ID of the starting step.")
    steps: dict[str, Step] = Field(..., description="Dictionary of all steps indexed by ID.")


class ManifestMetadata(CoReasonBaseModel):
    """
    Metadata for the manifest.

    Attributes:
        name (str): Human-readable name of the workflow/agent.
        generation_rationale (str | None): Reasoning behind the creation or selection of this workflow.
        confidence_score (float | None): A score (0.0 - 1.0) indicating the system's confidence in this workflow.
        original_user_intent (str | None): The original user prompt or goal that resulted in this workflow.
        generated_by (str | None): The model or system ID that generated this manifest (e.g., 'coreason-strategist-v1').
        design_metadata (DesignMetadata | None): UI metadata. (Alias: 'x-design').
        provenance (ProvenanceData | None): Provenance metadata.
        tested_models (list[str]): List of LLM identifiers this manifest has been tested on.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, frozen=True)

    name: str = Field(..., description="Human-readable name of the workflow/agent.")
    generation_rationale: str | None = Field(
        None, description="Reasoning behind the creation or selection of this workflow."
    )
    confidence_score: float | None = Field(
        None, ge=0.0, le=1.0, description="A score (0.0 - 1.0) indicating the system's confidence in this workflow."
    )
    original_user_intent: str | None = Field(
        None, description="The original user prompt or goal that resulted in this workflow."
    )
    generated_by: str | None = Field(
        None, description="The model or system ID that generated this manifest (e.g., 'coreason-strategist-v1')."
    )
    design_metadata: DesignMetadata | None = Field(None, description="UI metadata.")
    provenance: ProvenanceData | None = Field(None, description="Provenance metadata.")
    tested_models: list[str] = Field(
        default_factory=list, description="List of LLM identifiers this manifest has been tested on."
    )


# Import ToolPackDefinition after definitions are declared to avoid circular import

# Update forward references for ToolPackDefinition using the local namespace
ToolPackDefinition.model_rebuild(
    _types_namespace={"AgentDefinition": AgentDefinition, "ToolDefinition": ToolDefinition}
)


class ManifestV2(CoReasonBaseModel):
    """
    Root object for Coreason Manifest V2.

    Attributes:
        apiVersion (Literal["coreason.ai/v2"]): API Version. (Default: "coreason.ai/v2").
        kind (Literal["Recipe", "Agent"]): Kind of the object.
        metadata (ManifestMetadata): Metadata including name and design info.
        interface (InterfaceDefinition): Input/Output contract.
        state (StateDefinition): Internal state schema.
        policy (PolicyDefinition): Policy and governance.
        definitions (dict[str, ToolDefinition | AgentDefinition | ...]): Reusable definitions.
            (Polymorphic: Discriminator 'type').
        workflow (Workflow): The main workflow topology.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    apiVersion: Literal["coreason.ai/v2"] = Field("coreason.ai/v2", description="API Version.")  # noqa: N815
    kind: Literal["Recipe", "Agent"] = Field(..., description="Kind of the object.")
    metadata: ManifestMetadata = Field(..., description="Metadata including name and design info.")
    interface: InterfaceDefinition = Field(default_factory=InterfaceDefinition)
    state: StateDefinition = Field(default_factory=StateDefinition)
    policy: PolicyDefinition = Field(default_factory=PolicyDefinition)
    definitions: dict[
        str,
        Annotated[
            ToolDefinition | AgentDefinition | SkillDefinition | MCPResourceDefinition | ToolPackDefinition,
            Field(discriminator="type"),
        ]
        | GenericDefinition,
    ] = Field(default_factory=dict, description="Reusable definitions.")
    workflow: Workflow = Field(..., description="The main workflow topology.")

    @model_validator(mode="after")
    def check_integrity(self) -> Self:
        steps = self.workflow.steps

        # 1. Validate Start Step
        if self.workflow.start not in steps:
            raise ValueError(f"Start step '{self.workflow.start}' not found in steps.")

        for step in steps.values():
            # 2. Validate 'next' pointers (AgentStep, LogicStep, CouncilStep)
            if hasattr(step, "next") and step.next and step.next not in steps:
                raise ValueError(f"Step '{step.id}' references missing next step '{step.next}'.")

            # 3. Validate SwitchStep targets
            if isinstance(step, SwitchStep):
                for target in step.cases.values():
                    if target not in steps:
                        raise ValueError(f"SwitchStep '{step.id}' references missing step '{target}' in cases.")
                if step.default and step.default not in steps:
                    raise ValueError(
                        f"SwitchStep '{step.id}' references missing step '{step.default}' in default."
                    )

            # 4. Validate Definition References
            if isinstance(step, AgentStep):
                if step.agent not in self.definitions:
                    raise ValueError(f"AgentStep '{step.id}' references missing agent '{step.agent}'.")

                # Check type
                agent_def = self.definitions[step.agent]
                if not isinstance(agent_def, AgentDefinition):
                    raise ValueError(
                        f"AgentStep '{step.id}' references '{step.agent}' which is not an AgentDefinition "
                        f"(got {type(agent_def).__name__})."
                    )

            if isinstance(step, CouncilStep):
                for voter in step.voters:
                    if voter not in self.definitions:
                        raise ValueError(f"CouncilStep '{step.id}' references missing voter '{voter}'.")

                    # Check type
                    agent_def = self.definitions[voter]
                    if not isinstance(agent_def, AgentDefinition):
                        raise ValueError(
                            f"CouncilStep '{step.id}' references voter '{voter}' which is not an AgentDefinition "
                            f"(got {type(agent_def).__name__})."
                        )

        # 5. Validate Agent Tools
        for definition in self.definitions.values():
            if isinstance(definition, AgentDefinition):
                for tool_ref in definition.tools:
                    # Handle ToolRequirement (remote tools)
                    if isinstance(tool_ref, ToolRequirement):
                        if tool_ref.uri in self.definitions:
                            tool_def = self.definitions[tool_ref.uri]
                            if not isinstance(tool_def, ToolDefinition):
                                raise ValueError(
                                    f"Agent '{definition.id}' references '{tool_ref.uri}' which is not a ToolDefinition "
                                    f"(got {type(tool_def).__name__})."
                                )
                        elif "://" not in tool_ref.uri:
                            # If it's not a valid URI (no scheme) and not in definitions, assume broken ID reference
                            raise ValueError(f"Agent '{definition.id}' references missing tool '{tool_ref.uri}'.")

        return self
