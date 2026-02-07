# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Annotated, Any, Literal

from pydantic import ConfigDict, Field, field_validator

from coreason_manifest.spec.common.capabilities import AgentCapabilities
from coreason_manifest.spec.common.interoperability import AgentRuntimeConfig
from coreason_manifest.spec.common_base import CoReasonBaseModel, StrictUri, ToolRiskLevel
from coreason_manifest.spec.v2.contracts import InterfaceDefinition, PolicyDefinition, StateDefinition
from coreason_manifest.spec.v2.evaluation import EvaluationProfile
from coreason_manifest.spec.v2.resources import ModelProfile

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
    "Step",
    "SwitchStep",
    "ToolDefinition",
    "ToolRequirement",
    "Workflow",
]


class DesignMetadata(CoReasonBaseModel):
    """UI-specific metadata for the visual builder."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    x: float = Field(..., description="X coordinate on the canvas.")
    y: float = Field(..., description="Y coordinate on the canvas.")
    icon: str | None = Field(None, description="Icon name or URL.")
    color: str | None = Field(None, description="Color code (hex/name).")
    label: str | None = Field(None, description="Display label.")
    zoom: float | None = Field(None, description="Zoom level.")
    collapsed: bool = Field(False, description="Whether the node is collapsed in UI.")


class ToolDefinition(CoReasonBaseModel):
    """Definition of an external tool."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["tool"] = "tool"
    id: str = Field(..., description="Unique ID for the tool within the manifest.")
    name: str = Field(..., description="Name of the tool.")
    uri: StrictUri = Field(..., description="The MCP endpoint URI.")
    risk_level: ToolRiskLevel = Field(..., description="Risk level (safe, standard, critical).")
    description: str | None = Field(None, description="Description of the tool.")


class ToolRequirement(CoReasonBaseModel):
    """A requirement for a remote tool."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["remote"] = "remote"
    uri: str = Field(..., description="The URI of the tool or reference ID.")
    hash: str | None = Field(None, description="Optional integrity hash.")


class InlineToolDefinition(CoReasonBaseModel):
    """A tool defined directly within the manifest (Serverless/Local)."""

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
    """Definition of an Agent."""

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

    @field_validator("tools", mode="before")
    @classmethod
    def normalize_tools(cls, v: Any) -> Any:
        if not isinstance(v, list):
            return v

        normalized = []
        for item in v:
            if isinstance(item, str):
                normalized.append({"type": "remote", "uri": item})
            elif isinstance(item, dict):
                # If type is missing, assume remote if uri is present, or error out later
                if "type" not in item and "uri" in item:
                    # Default to remote for backward compatibility if it looks like one
                    # But InlineToolDefinition has mandatory fields that remote doesn't.
                    # Remote has mandatory 'uri'.
                    item = item.copy()
                    item["type"] = "remote"
                normalized.append(item)
            else:
                normalized.append(item)
        return normalized

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
    """Fallback for unknown definitions."""

    model_config = ConfigDict(extra="allow", frozen=True)


class BaseStep(CoReasonBaseModel):
    """Base attributes for all steps."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    id: str = Field(..., description="Unique identifier for the step.")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input arguments for the step.")
    design_metadata: DesignMetadata | None = Field(None, alias="x-design", description="UI metadata.")


class AgentStep(BaseStep):
    """A step that executes an AI Agent."""

    type: Literal["agent"] = "agent"
    agent: str = Field(..., description="Reference to an Agent definition (by ID or name).")
    next: str | None = Field(None, description="ID of the next step to execute.")
    system_prompt: str | None = Field(None, description="Optional override for system prompt.")


class LogicStep(BaseStep):
    """A step that executes custom logic."""

    type: Literal["logic"] = "logic"
    code: str = Field(..., description="Python code or reference to logic to execute.")
    next: str | None = Field(None, description="ID of the next step to execute.")


class CouncilStep(BaseStep):
    """A step that involves multiple voters/agents."""

    type: Literal["council"] = "council"
    voters: list[str] = Field(..., description="List of voters (Agent IDs).")
    strategy: str = Field("consensus", description="Voting strategy (e.g., consensus, majority).")
    next: str | None = Field(None, description="ID of the next step to execute.")


class SwitchStep(BaseStep):
    """A step that routes execution based on conditions."""

    type: Literal["switch"] = "switch"
    cases: dict[str, str] = Field(..., description="Dictionary of condition expressions to Step IDs.")
    default: str | None = Field(None, description="Default Step ID if no cases match.")
    # Note: 'next' is deliberately excluded for SwitchStep in favor of cases/default.


Step = Annotated[
    AgentStep | LogicStep | CouncilStep | SwitchStep,
    Field(discriminator="type", description="Polymorphic step definition."),
]


class Workflow(CoReasonBaseModel):
    """Defines the execution topology."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    start: str = Field(..., description="ID of the starting step.")
    steps: dict[str, Step] = Field(..., description="Dictionary of all steps indexed by ID.")


class ManifestMetadata(CoReasonBaseModel):
    """Metadata for the manifest."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, frozen=True)

    name: str = Field(..., description="Human-readable name of the workflow/agent.")
    design_metadata: DesignMetadata | None = Field(None, alias="x-design", description="UI metadata.")


class ManifestV2(CoReasonBaseModel):
    """Root object for Coreason Manifest V2."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    apiVersion: Literal["coreason.ai/v2"] = Field("coreason.ai/v2", description="API Version.")
    kind: Literal["Recipe", "Agent"] = Field(..., description="Kind of the object.")
    metadata: ManifestMetadata = Field(..., description="Metadata including name and design info.")
    interface: InterfaceDefinition = Field(default_factory=InterfaceDefinition)
    state: StateDefinition = Field(default_factory=StateDefinition)
    policy: PolicyDefinition = Field(default_factory=PolicyDefinition)
    definitions: dict[
        str,
        Annotated[ToolDefinition | AgentDefinition, Field(discriminator="type")] | GenericDefinition,
    ] = Field(default_factory=dict, description="Reusable definitions.")
    workflow: Workflow = Field(..., description="The main workflow topology.")
