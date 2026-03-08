# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:
This file defines the Scientific Visualization (SciVis) grammar. This is a STRICTLY PROJECTION BOUNDARY.
These schemas govern how multi-dimensional agent knowledge is collapsed and encoded for human perception.
YOU ARE EXPLICITLY FORBIDDEN from adding state-mutation or backend logic here.
Think purely in terms of declarative graphical grammars (Marks, Channels, Scales).
"""

import re
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

    type: Literal["linear", "log", "time", "ordinal", "nominal"] = Field(
        description="The mathematical scale mapping data to pixels."
    )
    domain_min: float | None = Field(default=None, description="The optional minimum bound of the scale domain.")
    domain_max: float | None = Field(default=None, description="The optional maximum bound of the scale domain.")


class ChannelEncoding(CoreasonBaseModel):
    """The visual property being manipulated."""

    channel: Literal["x", "y", "color", "size", "opacity", "shape", "text"] = Field(
        description="The visual channel the data is mapped to."
    )
    field: str = Field(description="The exact column or field name from the dataset.")
    scale: ScaleDefinition | None = Field(
        default=None, description="Optional scale override for this specific channel."
    )


class FacetMatrix(CoreasonBaseModel):
    """Optional small-multiple faceting layout."""

    row_field: str | None = Field(default=None, description="The dataset field used to split the chart into rows.")
    column_field: str | None = Field(
        default=None, description="The dataset field used to split the chart into columns."
    )


class GrammarPanel(CoreasonBaseModel):
    """Panel representing a deterministic, declarative visual grammar."""

    panel_id: str = Field(description="The unique identifier for this UI panel.")
    type: Literal["grammar"] = Field(default="grammar", description="Discriminator for Grammar of Graphics charts.")
    title: str = Field(description="The human-readable title of the chart.")
    data_source_id: str = Field(description="The cryptographic pointer to the dataset in the EpistemicLedger.")
    mark: Literal["point", "line", "area", "bar", "rect", "arc"] = Field(
        description="The geometric shape used to represent the data."
    )
    encodings: list[ChannelEncoding] = Field(description="The mapping of data fields to visual channels.")
    facet: FacetMatrix | None = Field(default=None, description="Optional faceting matrix for small multiples.")

    @model_validator(mode="after")
    def sort_encodings(self) -> Self:
        """Mathematically sorts self.encodings by the string value of channel for deterministic hashing."""
        object.__setattr__(self, "encodings", sorted(self.encodings, key=lambda e: e.channel))
        return self


class InsightCard(CoreasonBaseModel):
    """Panel displaying a semantic text summary."""

    panel_id: str = Field(description="The unique identifier for this UI panel.")
    type: Literal["insight_card"] = Field(
        default="insight_card", description="Discriminator for markdown insight cards."
    )
    title: str = Field(description="The human-readable title of the insight.")
    markdown_content: str = Field(description="The markdown formatted text content.")

    @field_validator("markdown_content")
    @classmethod
    def sanitize_markdown(cls, v: str) -> str:
        """Strictly restrict '<' to mathematical contexts to prevent XSS."""
        v_lower = v.lower()
        if re.search(r"on[a-zA-Z]+\s*=", v_lower):
            raise ValueError("Forbidden HTML event handler detected.")
        if re.search(r"<[^=\s\d]", v):
            raise ValueError(
                "HTML tags are prohibited. '<' may only be used as a mathematical operator "
                "followed by a space, digit, or '='."
            )
        return v


# =========================================================================
# AGENT INSTRUCTION: WARNING - POLYMORPHIC ROUTER
# If you create a new class above, you MUST append it to the AnyPanel union below.
# Failure to do so will result in a fatal Pydantic discriminator crash at runtime,
# creating a 'Dangling Class' that the orchestrator cannot deserialize.
# =========================================================================

type AnyPanel = Annotated[
    GrammarPanel | InsightCard,
    Field(discriminator="type", description="A discriminated union of presentation UI panels."),
]


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
        return self
