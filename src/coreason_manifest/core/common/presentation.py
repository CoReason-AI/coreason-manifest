from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class RenderStrategy(StrEnum):
    """
    Rendering strategies for Human-in-the-Loop interaction.
    """

    PLAIN_TEXT = "plain_text"
    JSON_FORMS = "json_forms"
    ADAPTIVE_CARD = "adaptive_card"
    CUSTOM_IFRAME = "custom_iframe"
    GEN_UI = "gen_ui"


class UIEventMap(CoreasonModel):
    trigger: str = Field(..., description="The name of the event emitted by the widget (e.g., 'on_approve').")
    action: str = Field(..., description="The semantic SteeringCommand or target route ID this translates to.")
    mutates_variables: list[str] | None = Field(None, description="Blackboard variables updated by this event.")
    payload_mapping: dict[str, str] | None = Field(
        default=None, description="Maps frontend widget event payload keys to specific Blackboard variable paths."
    )

    @model_validator(mode="after")
    def validate_zero_trust_mapping(self) -> "UIEventMap":
        if self.payload_mapping:
            if not self.mutates_variables:
                raise ValueError("payload_mapping requires mutates_variables to be defined.")
            for target_var in self.payload_mapping.values():
                if target_var not in self.mutates_variables:
                    raise ValueError(
                        f"Target variable '{target_var}' in payload_mapping is not allowed by mutates_variables."
                    )
        return self


class AdaptiveUIContract(CoreasonModel):
    widget_id: str = Field(..., description="The abstract identifier for the frontend component registry.")
    props_schema: dict[str, Any] = Field(
        ..., description="JSON Schema defining the data required to render the widget."
    )
    props_mapping: dict[str, str] = Field(
        default_factory=dict, description="Maps Blackboard variables (values) to widget props (keys)."
    )
    events: list[UIEventMap] = Field(
        default_factory=list, description="Maps widget interactions to orchestrator commands."
    )
    fallback_to_text: bool = Field(
        True, description="Gracefully degrade to JSON Form or Text input if widget is unavailable."
    )


class NotificationRouting(CoreasonModel):
    """
    Routing configuration for human interventions.
    """

    channels: list[str] = Field(default_factory=list, description="e.g., ['slack', 'email', 'push']")
    urgency: Literal["low", "medium", "high", "critical"] = Field(default="medium")


class NodeColor(StrEnum):
    """
    Semantic coloring for the graph.
    """

    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"
    GREY = "grey"


class GuiCoords(CoreasonModel):
    """
    X/Y coordinates to persist the layout of the graph in the visual editor.
    """

    x: float
    y: float


class PresentationHints(CoreasonModel):
    """
    Presentation Layer metadata for UI rendering.
    Allows backend logic to drive frontend visualization.
    """

    label: Annotated[
        str | None,
        Field(
            description=(
                "A human-readable name for the node (e.g., 'Review Analyst'). Used by the UI and the Graph Visualizer."
            )
        ),
    ] = None

    description: Annotated[
        str | None,
        Field(
            description=(
                "A documentation string. Crucially, this is dual-purpose: "
                "1. Human: Tooltips in the Builder UI. "
                "2. Machine: Injected into the System Prompt so the LLM understands the 'Intent' of the node "
                "it is executing."
            )
        ),
    ] = None

    icon: Annotated[
        str | None,
        Field(description="Likely an SVG path or a library identifier (e.g., lucide-react name) for the visualizer."),
    ] = None

    color: Annotated[
        NodeColor | None,
        Field(description="Semantic coloring for the graph (e.g., 'Red' for Critical Gates, 'Blue' for Actions)."),
    ] = None

    gui_coords: Annotated[
        GuiCoords | None,
        Field(description="X/Y coordinates to persist the layout of the graph in the visual editor."),
    ] = None

    style: Annotated[
        dict[str, str] | None,
        Field(description="CSS-like properties (color, shape, etc.)."),
    ] = None

    group: Annotated[str | None, Field(description="For visual clustering/subgraphs.")] = None

    hidden: Annotated[bool, Field(description="Whether the node should be hidden in default views.")] = False

    metadata_view: Annotated[
        Literal["basic", "detailed", "debug"],
        Field(description="Preferred metadata detail level."),
    ] = "basic"
