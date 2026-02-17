from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class PresentationHints(BaseModel):
    """
    Presentation Layer metadata for UI rendering.
    Allows backend logic to drive frontend visualization.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    label: Annotated[str | None, Field(description="Human-readable name for the node.")] = None
    icon: Annotated[str | None, Field(description="Icon identifier (e.g., 'lucide:shield-check').")] = None
    style: Annotated[dict[str, str] | None, Field(description="CSS-like properties (color, shape, etc.).")] = None
    group: Annotated[str | None, Field(description="For visual clustering/subgraphs.")] = None
    hidden: Annotated[bool, Field(description="Whether the node should be hidden in default views.")] = False
    metadata_view: Annotated[Literal["basic", "detailed", "debug"], Field(description="Preferred metadata detail level.")] = "basic"
