from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class BasePanel(CoreasonBaseModel):
    """Base class for Scientific Visualization panels."""


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


type AnyPanel = Annotated[TimeSeriesPanel | CohortAttritionGrid | InsightCard, Field(discriminator="type")]


class MacroGrid(CoreasonBaseModel):
    """A layout matrix containing a list of panels."""

    layout_matrix: list[list[str]] = Field(description="A matrix defining the layout structure, using panel IDs.")
    panels: list[AnyPanel] = Field(description="A list of panels included in the grid.")
