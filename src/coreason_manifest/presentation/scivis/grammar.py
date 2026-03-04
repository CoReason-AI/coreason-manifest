# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Literal

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel


class GrammarOfGraphicsSpecification(CoreasonModel):
    """
    Represents a Vega-Lite or Apache ECharts inspired declarative visualization contract.
    This pure data schema dictates the visual mappings for data arrays provided externally.
    External executing environments (like an MS Teams Adaptive Card or Excel native chart)
    must interpret this contract to generate the UI components.
    """

    vis_id: str = Field(..., description="A unique UUID string identifying this visualization.")
    title: str = Field(..., description="The title of the visualization.")
    description: str = Field(
        ..., description="Description explaining the epidemiological insight of the visualization."
    )
    mark_type: Literal["LINE", "BAR", "POINT", "AREA", "TICK"] = Field(
        ..., description="The visual mark type to use (e.g. LINE, BAR, POINT, AREA, TICK)."
    )
    data_bindings: dict[str, str] = Field(
        ..., description="Dictionary mapping string keys to expected data structures or OMOP column names."
    )
    encoding: dict[str, str] = Field(
        ..., description="Dictionary mapping visual channels like `x`, `y`, `color`, `tooltip` to data fields."
    )


class TimelineVisContract(CoreasonModel):
    """
    A specialized schema for rendering OMOP patient trajectories or cohort attrition timelines.
    This structure embeds a base GrammarOfGraphicsSpecification.
    """

    trajectory_id: str = Field(..., description="Identifier for the trajectory.")
    time_zero_event: str = Field(..., description="Description of the index date (time zero) event.")
    events: list[dict[str, Any]] = Field(
        ...,
        description=(
            "A list of dictionaries representing events in the timeline, expected to "
            "contain `event_name`, `days_from_index`, and `event_domain`."
        ),
    )
    base_specification: GrammarOfGraphicsSpecification = Field(
        ..., description="Reference to a GrammarOfGraphicsSpecification base contract."
    )
