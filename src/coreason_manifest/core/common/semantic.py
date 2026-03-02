# Prosperity-3.0
from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import ConfigDict, Field

from coreason_manifest.core.common.base import CoreasonModel


class OptimizationIntent(CoreasonModel):
    """Directives for Weaver synthesis optimization."""

    model_config = ConfigDict(frozen=True)

    improvement_goal: str = Field(
        ...,
        description="Prompt for the Weaver/Optimizer (e.g., 'Reduce hallucinations').",
        examples=["Reduce hallucinations", "Maximize throughput"],
    )
    metric_name: str = Field(
        ...,
        description="Grading function to optimize against (e.g., 'faithfulness').",
        examples=["faithfulness", "accuracy"],
    )
    teacher_model: str | None = Field(
        None,
        description="Model to use for synthetic bootstrapping.",
        examples=["gpt-4"],
    )
    max_demonstrations: int = Field(
        default=5,
        ge=0,
        description="Maximum number of few-shot examples to learn and inject.",
    )


class SemanticRef(CoreasonModel):
    """Abstract Semantic Tree placeholder for Intent-Based Orchestration (IBO)."""

    model_config = ConfigDict(frozen=True)

    intent: str = Field(
        ...,
        description="Natural language description of the required agent or tool's goal.",
        examples=["Retrieve current stock prices", "Analyze sentiment of the given text"],
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Hard system or compliance requirements.",
        examples=[["must be HIPAA compliant", "latency < 200ms"]],
    )
    optimization: OptimizationIntent | None = Field(
        None,
        description="Directives for Weaver synthesis optimization.",
    )
    candidates: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Stores AI-driven catalog search results (candidates) before final resolution.",
    )


class PICOClass(StrEnum):
    POPULATION = "population"
    INTERVENTION = "intervention"
    COMPARISON = "comparison"
    OUTCOME = "outcome"
    STUDY_DESIGN = "study_design"


class SearchTermType(StrEnum):
    CONTROLLED_VOCAB = "controlled_vocab"
    FREE_TEXT = "free_text"


class PICOOperator(StrEnum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    PROXIMITY = "PROXIMITY"


class PICOLeafNode(CoreasonModel):
    """An atomic search term decoupled from database-specific syntax."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["leaf"] = "leaf"
    pico_class: Annotated[PICOClass | None, Field(description="The PICO category this term belongs to.")] = None
    term: Annotated[str, Field(description="The exact search string or ontology ID (e.g., 'D006339' or 'Heart Failure').")]
    term_type: Annotated[SearchTermType, Field(description="Whether this is a controlled term (e.g. MeSH) or free text.")]
    explode: Annotated[bool, Field(description="If True, search all narrower terms in the ontology tree.")] = False
    truncate: Annotated[bool, Field(description="If True, apply wildcard truncation to the term.")] = False
    field_restrictions: Annotated[list[str] | None, Field(description="Specific fields to search (e.g., ['tiab', 'tw']).")] = None


class PICOOperatorNode(CoreasonModel):
    """A recursive boolean or proximity combinator."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["operator"] = "operator"
    operator: Annotated[PICOOperator, Field(description="The logic operator applied to the children.")]
    proximity_distance: Annotated[int | None, Field(description="Distance 'n' required if operator is PROXIMITY.")] = None
    children: Annotated[list['PICONode'], Field(description="Child nodes connected by this operator.")]


# Discriminated Union for recursive tree walking
PICONode = Annotated[PICOLeafNode | PICOOperatorNode, Field(discriminator="type")]


class PICOASTConfig(CoreasonModel):
    """Contract enforcing that an agent outputs a structured PICO AST rather than raw text."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    enforce_pico_ast: Annotated[bool, Field(description="If True, the agent must output a valid PICONode JSON tree.")] = True
    default_operator: Annotated[PICOOperator, Field(description="The default operator to combine disjoint PICO classes at the root.")] = PICOOperator.AND


__all__ = [
    "OptimizationIntent",
    "SemanticRef",
    "PICOClass",
    "SearchTermType",
    "PICOOperator",
    "PICOLeafNode",
    "PICOOperatorNode",
    "PICONode",
    "PICOASTConfig",
]
