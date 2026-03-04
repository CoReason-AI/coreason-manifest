"""
Model Context Protocol (MCP) Primitives for Health Informatics and Observational Research.

This module defines state-of-the-art MCP primitives acting as the definitive schema
contracts for external execution environments interacting with the OMOP Common Data
Model and the OHDSI open-science collaborative ecosystem.

These structures are pure, passive contracts. An external MCP server uses them to
securely expose OMOP standard constructs to an AI agent, wrap open-source execution
software (like CohortDiagnostics), and treat prompt engineering as a reproducible
scientific artifact.
"""

import re
from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator

from coreason_manifest.core.common.base import CoreasonModel


class OMOPDomain(StrEnum):
    """
    Standard OMOP domains for resource types.
    """

    CONCEPT = "CONCEPT"
    COHORT_DEFINITION = "COHORT_DEFINITION"
    CONCEPT_ANCESTOR = "CONCEPT_ANCESTOR"
    PHENOTYPE_EVALUATION = "PHENOTYPE_EVALUATION"


class OMOPResourceTemplate(CoreasonModel):
    """
    Represents an MCP Resource Template exposing OMOP standard constructs to an AI agent securely.

    An external MCP server will utilize this contract to advertise available epidemiological
    data resources. The AI agent populates the template variables to request specific OMOP
    concepts, cohorts, or other supported analytical constructs.
    """

    uri_template: str = Field(
        ...,
        description="The URI template for the resource, matching an omop:// protocol pattern.",
    )
    resource_type: OMOPDomain = Field(
        ...,
        description="The standard OMOP domain for the resource.",
    )
    description: str = Field(
        ...,
        description="Documents exactly what epidemiological data this resource yields.",
    )

    @field_validator("uri_template")
    @classmethod
    def validate_uri_template(cls, v: str) -> str:
        """Ensure the URI template strictly matches the omop:// protocol pattern."""
        if not re.match(r"^omop://(?:[a-zA-Z0-9_/-]+|/\{[a-zA-Z0-9_]+\})+$", v):
            raise ValueError("uri_template must follow the 'omop://' protocol pattern")
        return v


class CohortDiagnosticsRequest(CoreasonModel):
    """
    Declarative input contract for an MCP Tool wrapping OHDSI CohortDiagnostics software.

    The AI agent populates this schema with the necessary analytical parameters. A separate
    execution server reads this passive contract and maps it directly to the underlying
    R package function arguments to execute OHDSI CohortDiagnostics.
    """

    inclusion_rules: tuple[str | Mapping[str, Any], ...] = Field(
        ...,
        description="Array of heavily typed JSON-logic or criteria string representations.",
    )
    target_cohort_ids: tuple[int, ...] = Field(
        ...,
        description="List of target cohort IDs.",
    )
    comparator_cohort_ids: tuple[int, ...] | None = Field(
        default=None,
        description="Optional list of comparator cohort IDs.",
    )
    evaluation_windows: tuple[int, ...] = Field(
        ...,
        description="List of integers representing days (e.g., [0, 30, 365]).",
    )
    diagnostic_flags: Mapping[str, bool] = Field(
        ...,
        description="Mapping of string flags to booleans, matching the R package's execution parameters.",
    )


class EpistemicPromptManifest(CoreasonModel):
    """
    MCP Prompt specifically bounded for phenotype development and clinical reasoning.

    Treats prompt engineering as a reproducible scientific artifact. An external MCP server
    uses this contract to supply the AI agent with a rigorously defined prompt structure
    for health informatics tasks, ensuring that outputs strictly adhere to required guidelines
    and scientific rigor.
    """

    prompt_id: str = Field(
        ...,
        description="The unique identifier for the prompt.",
    )
    version: str = Field(
        ...,
        description="The version string of the prompt.",
    )
    instruction_template: str = Field(
        ...,
        description="The core LLM directive.",
    )
    required_guideline_citations: bool = Field(
        ...,
        description="Indicates if the LLM must provide W3C PROV-O structured citations in its output.",
    )
    expected_output_schema: str = Field(
        ...,
        description="Reference to the Pydantic model the LLM must return.",
    )
    reproducibility_hash: str = Field(
        ...,
        description="Cryptographically locks the exact phrasing of the prompt for peer-reviewed publication tracking.",
    )
