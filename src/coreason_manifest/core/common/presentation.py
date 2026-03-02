from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.state.ephemeral import LocalStateManifest

from .client_actions import ClientActionMap
from .highlighting import HighlightConfig
from .search_layout import HybridSearchLayout
from .suspense import SuspenseConfig
from .templating import ParameterizedDataRef
from .transform import DataTransformSchema
from .typeahead import TypeaheadConfig
from .validation import UIValidationSchema


class RenderStrategy(StrEnum):
    """
    Rendering strategies for Human-in-the-Loop interaction.
    """

    PLAIN_TEXT = "plain_text"
    JSON_FORMS = "json_forms"
    ADAPTIVE_CARD = "adaptive_card"
    CUSTOM_IFRAME = "custom_iframe"
    GEN_UI = "gen_ui"
    MCP_APPS = "mcp_apps"


class UIEventMap(CoreasonModel):
    trigger: str = Field(..., description="The name of the event emitted by the widget (e.g., 'on_approve').")
    action: str = Field(..., description="The semantic SteeringCommand or target route ID this translates to.")
    mutates_variables: list[str] | None = Field(None, description="Blackboard variables updated by this event.")
    payload_mapping: dict[str, str] | None = Field(
        default=None, description="Maps frontend widget event payload keys to specific Blackboard variable paths."
    )

    @model_validator(mode="after")
    def validate_zero_trust_mapping(self) -> "UIEventMap":
        """Enforce that payload_mapping requires mutates_variables and targets are allowed."""
        if self.payload_mapping:
            if not self.mutates_variables:
                raise ValueError("payload_mapping requires mutates_variables to be defined.")
            for target_var in self.payload_mapping.values():
                if target_var not in self.mutates_variables:
                    raise ValueError(
                        f"Target variable '{target_var}' in payload_mapping is not allowed by mutates_variables."
                    )
        return self


class UIComponentNode(CoreasonModel):
    type: str = Field(..., description="The component registry ID, e.g., 'LineChart', 'DataTable'.")
    props: dict[str, Any] = Field(
        default_factory=dict, description="The evaluated property data to bind to the widget."
    )
    children: list["UIComponentNode"] = Field(
        default_factory=list, description="Child component nodes for recursive nesting."
    )
    client_actions: list[ClientActionMap] = Field(
        default_factory=list, description="Native OS-level actions triggered by client gestures."
    )
    validation: UIValidationSchema | None = Field(
        default=None, description="Client-side validation rules for edge-fencing."
    )
    suspense: SuspenseConfig | None = Field(
        default=None, description="Skeleton layout configuration while waiting for data."
    )
    local_state: LocalStateManifest | None = Field(
        default=None, description="Ephemeral Scratchpad memory for this component."
    )
    data_ref: ParameterizedDataRef | None = Field(
        default=None, description="Reactive data source for out-of-band fetching."
    )
    data_transform: DataTransformSchema | None = Field(
        default=None, description="Edge-computed filtering/sorting rules."
    )
    typeahead: TypeaheadConfig | None = Field(default=None, description="Fast-path autocomplete configuration.")
    highlighting: HighlightConfig | None = Field(default=None, description="Client-side text highlighting rules.")


class AdaptiveUIContract(CoreasonModel):
    layout: list[UIComponentNode] = Field(default_factory=list, description="The root elements of the generated UI.")
    widget_id: str | None = Field(
        None, description="[DEPRECATED] The abstract identifier for the frontend component registry."
    )
    props_schema: dict[str, Any] | None = Field(
        None, description="[DEPRECATED] JSON Schema defining the data required to render the widget."
    )
    props_mapping: dict[str, str] = Field(
        default_factory=dict, description="[DEPRECATED] Maps Blackboard variables (values) to widget props (keys)."
    )
    events: list[UIEventMap] = Field(
        default_factory=list, description="Maps widget interactions to orchestrator commands."
    )
    fallback_to_text: bool = Field(
        True, description="Gracefully degrade to JSON Form or Text input if widget is unavailable."
    )
    mcp_ui_resource_uri: str | None = Field(
        default=None,
        description="The ui:// scheme URI pointing to the bundled HTML/JS for sandboxed execution (SEP-1865).",
    )
    hybrid_search: HybridSearchLayout | None = Field(
        default=None, description="Bipartite search layout for side-by-side Lexical/Semantic results."
    )

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_widget(cls, data: Any) -> Any:
        """Migrate legacy widget dictionary structure to layout nodes."""
        if isinstance(data, dict):
            layout = data.get("layout")
            widget_id = data.get("widget_id")

            # If layout is empty/missing but widget_id is provided, auto-migrate to the new structure
            if not layout and widget_id:
                props = data.get("props_mapping", {})
                node = {"type": widget_id, "props": props, "children": []}
                data["layout"] = [node]
        return data


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


UIComponentNode.model_rebuild()
