from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel


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
            description="A human-readable name for the node (e.g., 'Review Analyst'). Used by the UI and the Graph Visualizer."
        ),
    ] = None

    description: Annotated[
        str | None,
        Field(
            description=(
                "A documentation string. Crucially, this is dual-purpose: "
                "1. Human: Tooltips in the Builder UI. "
                "2. Machine: Injected into the System Prompt so the LLM understands the 'Intent' of the node it is executing."
            )
        ),
    ] = None

    icon: Annotated[
        str | None,
        Field(
            description="Likely an SVG path or a library identifier (e.g., lucide-react name) for the visualizer."
        ),
    ] = None

    color: Annotated[
        NodeColor | None,
        Field(
            description="Semantic coloring for the graph (e.g., 'Red' for Critical Gates, 'Blue' for Actions)."
        ),
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

    hidden: Annotated[
        bool, Field(description="Whether the node should be hidden in default views.")
    ] = False

    metadata_view: Annotated[
        Literal["basic", "detailed", "debug"],
        Field(description="Preferred metadata detail level."),
    ] = "basic"
