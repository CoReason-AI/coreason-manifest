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


class TimeSeriesPanel(BasePanel):
    """Panel representing a time-series chart."""

    type: Literal["timeseries"] = Field(default="timeseries", description="Discriminator for a time-series panel.")
    x_axis_label: str = Field(description="The label for the x-axis.")
    y_axis_label: str = Field(description="The label for the y-axis.")
    data_series: list[dict[str, str | int | float]] = Field(
        description="A list of data points representing the time-series data."
    )


class CohortAttritionGrid(BasePanel):
    """Panel representing a table or grid of cohort data attrition."""

    type: Literal["cohort_attrition"] = Field(
        default="cohort_attrition",
        description="Discriminator for a cohort attrition grid.",
    )
    grid_data: list[dict[str, str | int | float]] = Field(
        description="A list of data rows representing cohort attrition over steps."
    )


class InsightCard(BasePanel):
    """Panel displaying a semantic text summary."""

    type: Literal["insight_card"] = Field(default="insight_card", description="Discriminator for an insight card.")
    title: str = Field(description="The title of the insight card.")
    markdown_content: str = Field(description="The semantic text summary written in Markdown.")

    @field_validator("markdown_content")
    @classmethod
    def sanitize_markdown(cls, v: str) -> str:
        """Reject adversarial HTML tags."""
        forbidden_tags = ["<script", "<iframe", "javascript:"]
        for tag in forbidden_tags:
            if tag in v.lower():
                raise ValueError(f"Forbidden HTML tag detected: {tag}")
        return v


type AnyPanel = Annotated[TimeSeriesPanel | CohortAttritionGrid | InsightCard, Field(discriminator="type")]


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
