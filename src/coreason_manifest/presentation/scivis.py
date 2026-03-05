# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from coreason_manifest.core.base import CoreasonBaseModel


class BasePanel(CoreasonBaseModel):
    """Base class for Scientific Visualization panels."""

    panel_id: str = Field(description="Unique identifier for the panel.")


type MarkType = Literal["point", "line", "area", "bar", "rect", "arc"]
type ScaleType = Literal["linear", "log", "time", "ordinal", "nominal"]
type EncodingChannel = Literal["x", "y", "color", "size", "opacity", "shape", "text"]


class ScaleDefinition(CoreasonBaseModel):
    """The mathematical mapping constraint for a channel."""

    type: ScaleType = Field(description="The mathematical scaling function.")
    domain_min: float | None = Field(default=None, description="Optional hard floor for the scale.")
    domain_max: float | None = Field(default=None, description="Optional hard ceiling for the scale.")


class ChannelEncoding(CoreasonBaseModel):
    """The visual property being manipulated."""

    channel: EncodingChannel = Field(description="The visual property being manipulated.")
    field: str = Field(description="The exact data key/column to bind to this channel.")
    scale: ScaleDefinition | None = Field(
        default=None, description="The mathematical mapping constraint for this channel."
    )


class FacetMatrix(CoreasonBaseModel):
    """Optional small-multiple faceting layout."""

    row_field: str | None = Field(default=None, description="Categorical field to split into rows.")
    column_field: str | None = Field(default=None, description="Categorical field to split into columns.")


class GrammarPanel(BasePanel):
    """Panel representing a deterministic, declarative visual grammar."""

    type: Literal["grammar"] = Field(default="grammar", description="Discriminator for a grammar panel.")
    title: str = Field(description="The title of the visualization.")
    data_source_id: str = Field(description="Pointer to the data matrix being visualized.")
    mark: MarkType = Field(description="The geometric primitive representing the data points.")
    encodings: list[ChannelEncoding] = Field(default_factory=list, description="The array of visual bindings.")
    facet: FacetMatrix | None = Field(default=None, description="Optional small-multiple faceting layout.")

    @model_validator(mode="after")
    def sort_encodings(self) -> Self:
        """Mathematically sorts self.encodings by the string value of channel for deterministic hashing."""
        object.__setattr__(self, "encodings", sorted(self.encodings, key=lambda e: e.channel))
        if hasattr(self, "_cached_hash"):
            object.__delattr__(self, "_cached_hash")
        return self


class InsightCard(BasePanel):
    """Panel displaying a semantic text summary."""

    type: Literal["insight_card"] = Field(default="insight_card", description="Discriminator for an insight card.")
    title: str = Field(description="The title of the insight card.")
    markdown_content: str = Field(max_length=50000, description="The semantic text summary written in Markdown.")

    @field_validator("markdown_content")
    @classmethod
    def sanitize_markdown(cls, v: str) -> str:
        """Reject adversarial HTML tags."""
        forbidden_tags = ["<script", "<iframe", "javascript:"]
        for tag in forbidden_tags:
            if tag in v.lower():
                raise ValueError(f"Forbidden HTML tag detected: {tag}")
        return v


type AnyPanel = Annotated[GrammarPanel | InsightCard, Field(discriminator="type")]


class MacroGrid(CoreasonBaseModel):
    """A layout matrix containing a list of panels."""

    layout_matrix: list[list[str]] = Field(description="A matrix defining the layout structure, using panel IDs.")
    panels: list[AnyPanel] = Field(description="A list of panels included in the grid.")

    @model_validator(mode="after")
    def verify_referential_integrity(self) -> Self:
        """Verify that all panel IDs referenced in layout_matrix exist in panels."""
        panel_ids = {panel.panel_id for panel in self.panels}
        for row in self.layout_matrix:
            for panel_id in row:
                if panel_id not in panel_ids:
                    raise ValueError(f"Ghost Panel referenced in layout_matrix: {panel_id}")
        if hasattr(self, "_cached_hash"):
            object.__delattr__(self, "_cached_hash")
        return self
