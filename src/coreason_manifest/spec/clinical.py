# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class ConceptSet(CoreasonBaseModel):
    """A strict schema representing a defined set of clinical concepts."""

    vocabulary_id: str = Field(description="The identifier for the vocabulary used.")
    concept_ids: list[str] = Field(description="A list of specific concept IDs.")
    descriptions: list[str] = Field(description="Text descriptions corresponding to the concept IDs.")


class CohortDefinition(CoreasonBaseModel):
    """A pure ontology definition of a clinical cohort."""

    inclusion_rules: list[str] = Field(description="The rules defining criteria for inclusion in the cohort.")
    exclusion_rules: list[str] = Field(description="The rules defining criteria for exclusion from the cohort.")
    observation_windows: list[int] = Field(description="Observation windows in days relative to an index event.")


class ObservationRecord(CoreasonBaseModel):
    """A record representing a clinical observation for a specific patient."""

    patient_id: str = Field(description="A reference identifier to the patient.")
    date: str = Field(description="The date of the observation in ISO 8601 format.")
    semantic_value: str = Field(description="The semantic clinical value of the observation.")
