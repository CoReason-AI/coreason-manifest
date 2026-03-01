# Prosperity-3.0
from pydantic import ConfigDict, Field

from coreason_manifest.core.common_base import CoreasonModel


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
        examples=[{"improvement_goal": "Maximize throughput", "metric_name": "accuracy", "teacher_model": "gpt-4"}],
    )
