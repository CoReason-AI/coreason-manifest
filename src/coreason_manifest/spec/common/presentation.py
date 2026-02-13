from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PresentationHints(BaseModel):
    """
    Presentation Layer metadata for UI rendering.
    Allows backend logic to drive frontend visualization.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    label: str | None = Field(None, description="Human-readable name for the node.")
    icon: str | None = Field(None, description="Icon identifier (e.g., 'lucide:shield-check').")
    style: dict[str, str] | None = Field(None, description="CSS-like properties (color, shape, etc.).")
    group: str | None = Field(None, description="For visual clustering/subgraphs.")
    hidden: bool = Field(False, description="Whether the node should be hidden in default views.")
    metadata_view: Literal["basic", "detailed", "debug"] = Field(
        "basic", description="Preferred metadata detail level."
    )
