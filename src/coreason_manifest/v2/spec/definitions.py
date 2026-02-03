from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.common import StrictUri, ToolRiskLevel
from coreason_manifest.v2.spec.contracts import InterfaceDefinition, PolicyDefinition, StateDefinition


class DesignMetadata(BaseModel):
    """UI-specific metadata for the visual builder."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    x: float = Field(..., description="X coordinate on the canvas.")
    y: float = Field(..., description="Y coordinate on the canvas.")
    icon: Optional[str] = Field(None, description="Icon name or URL.")
    color: Optional[str] = Field(None, description="Color code (hex/name).")
    label: Optional[str] = Field(None, description="Display label.")
    zoom: Optional[float] = Field(None, description="Zoom level.")
    collapsed: bool = Field(False, description="Whether the node is collapsed in UI.")


class ToolDefinition(BaseModel):
    """Definition of an external tool."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(..., description="Unique ID for the tool within the manifest.")
    name: str = Field(..., description="Name of the tool.")
    uri: StrictUri = Field(..., description="The MCP endpoint URI.")
    risk_level: ToolRiskLevel = Field(..., description="Risk level (safe, standard, critical).")
    description: Optional[str] = Field(None, description="Description of the tool.")


class BaseStep(BaseModel):
    """Base attributes for all steps."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(..., description="Unique identifier for the step.")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input arguments for the step.")
    design_metadata: Optional[DesignMetadata] = Field(None, alias="x-design", description="UI metadata.")


class AgentStep(BaseStep):
    """A step that executes an AI Agent."""

    type: Literal["agent"] = "agent"
    agent: str = Field(..., description="Reference to an Agent definition (by ID or name).")
    next: Optional[str] = Field(None, description="ID of the next step to execute.")
    system_prompt: Optional[str] = Field(None, description="Optional override for system prompt.")


class LogicStep(BaseStep):
    """A step that executes custom logic."""

    type: Literal["logic"] = "logic"
    code: str = Field(..., description="Python code or reference to logic to execute.")
    next: Optional[str] = Field(None, description="ID of the next step to execute.")


class CouncilStep(BaseStep):
    """A step that involves multiple voters/agents."""

    type: Literal["council"] = "council"
    voters: List[str] = Field(..., description="List of voters (Agent IDs).")
    strategy: str = Field("consensus", description="Voting strategy (e.g., consensus, majority).")
    next: Optional[str] = Field(None, description="ID of the next step to execute.")


class SwitchStep(BaseStep):
    """A step that routes execution based on conditions."""

    type: Literal["switch"] = "switch"
    cases: Dict[str, str] = Field(..., description="Dictionary of condition expressions to Step IDs.")
    default: Optional[str] = Field(None, description="Default Step ID if no cases match.")
    # Note: 'next' is deliberately excluded for SwitchStep in favor of cases/default.


Step = Annotated[
    Union[AgentStep, LogicStep, CouncilStep, SwitchStep],
    Field(discriminator="type", description="Polymorphic step definition."),
]


class Workflow(BaseModel):
    """Defines the execution topology."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    start: str = Field(..., description="ID of the starting step.")
    steps: Dict[str, Step] = Field(..., description="Dictionary of all steps indexed by ID.")


class ManifestMetadata(BaseModel):
    """Metadata for the manifest."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: str = Field(..., description="Human-readable name of the workflow/agent.")
    design_metadata: Optional[DesignMetadata] = Field(None, alias="x-design", description="UI metadata.")


class ManifestV2(BaseModel):
    """Root object for Coreason Manifest V2."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    apiVersion: Literal["coreason.ai/v2"] = Field("coreason.ai/v2", description="API Version.")
    kind: Literal["Recipe", "Agent"] = Field(..., description="Kind of the object.")
    metadata: ManifestMetadata = Field(..., description="Metadata including name and design info.")
    interface: InterfaceDefinition = Field(default_factory=InterfaceDefinition)
    state: StateDefinition = Field(default_factory=StateDefinition)
    policy: PolicyDefinition = Field(default_factory=PolicyDefinition)
    definitions: Dict[str, Union[ToolDefinition, Any]] = Field(
        default_factory=dict, description="Reusable definitions."
    )
    workflow: Workflow = Field(..., description="The main workflow topology.")
