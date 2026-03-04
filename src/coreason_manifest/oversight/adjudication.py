# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from collections.abc import Sequence
from typing import Literal

from pydantic import Field

from coreason_manifest.compute.argumentation import ArgumentationDAG
from coreason_manifest.compute.uncertainty import EpistemicWeight
from coreason_manifest.core.common.base import CoreasonModel


class AdjudicationOption(CoreasonModel):
    """
    Represents a specific choice in an adjudication form.
    """

    option_id: str = Field(..., description="The unique identifier for the option.")
    clinical_justification: str = Field(..., description="The clinical justification for the option.")


class AdjudicationFormContract(CoreasonModel):
    """
    Represents a structured "Interrupt" where the AI pauses execution and asks a human expert
    for guidance (e.g., via an MS Teams Adaptive Card). It specifies why it is uncertain
    and the available multiple-choice options for the human to select from.
    External applications interpret this declarative contract to render interactive forms.
    """

    adjudication_id: str = Field(..., description="A unique UUID string identifying this adjudication contract.")
    urgency_level: Literal["LOW", "MEDIUM", "HIGH", "BLOCKING"] = Field(
        ..., description="The urgency level for the requested human intervention."
    )
    epistemic_context: str = Field(
        ..., description="String explaining exactly *why* the AI is uncertain and requires human input."
    )
    uncertain_concepts: Sequence[str] = Field(
        ..., description="Sequence of strings representing the ambiguous clinical terms or OMOP concept IDs."
    )
    proposed_options: list[AdjudicationOption] = Field(
        ...,
        description=("Sequence of AdjudicationOption representing the multi-choice options the human can select."),
    )
    optional_debate_context: ArgumentationDAG | None = Field(
        default=None,
        description="Optional link to the argumentation DAG that caused the AI swarm to fail to reach consensus.",
    )
    requires_consensus: bool = Field(
        ..., description="Boolean indicating if multiple humans must respond before the workflow resumes."
    )


class AmbientInsightContract(CoreasonModel):
    """
    Represents a passive, non-blocking notification (e.g., an Excel cell highlight or subtle sidebar alert).
    It defines an alert that does not pause AI execution, but highlights an anomaly or suggested action.
    """

    insight_id: str = Field(..., description="A unique UUID string identifying this ambient insight.")
    target_ui_element: str = Field(..., description="String reference to what the external app should anchor this to.")
    anomaly_type: Literal["STATISTICAL_DEVIATION", "BIAS_DETECTED", "LITERATURE_CONFLICT"] = Field(
        ..., description="The classification of the detected anomaly."
    )
    mathematical_deviation: float = Field(..., description="Float representing the magnitude of the anomaly.")
    suggested_review_action: str = Field(..., description="Suggested action for the user to review the finding.")
    confidence_vector: EpistemicWeight | None = Field(
        default=None,
        description="Confidence weight associated with this ambient insight.",
    )
