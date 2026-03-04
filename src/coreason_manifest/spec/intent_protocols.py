# Prosperity-3.0
from typing import Literal

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel


class ConstraintConfig(CoreasonModel):
    """
    Defines hard execution boundaries for a routed intent.
    This establishes the 2026 SOTA compliance and performance limits
    before an intent is allowed to instantiate in a given environment.
    """

    max_latency_ms: int = Field(
        ...,
        description="The maximum allowed execution time in milliseconds before the intent is considered failed.",
        examples=[5000],
    )
    requires_hipaa_compliance: bool = Field(
        ...,
        description="Whether the target ecosystem must be certified for handling Protected Health Information (PHI).",
        examples=[True],
    )
    allowed_compute_regions: list[str] = Field(
        ...,
        description="A list of approved geographical or logical regions where compute can be allocated.",
        examples=[["us-east-1", "eu-west-1"]],
    )


class GracefulDegradationPolicy(CoreasonModel):
    """
    Dictates how an intent degrades if a strict catalog match fails.
    This enables resilient intent routing by falling back to relaxed constraints
    or alternative bootstrapping mechanisms under load.
    """

    droppable_constraints: list[str] = Field(
        ...,
        description="A list of field names in ConstraintConfig that can be safely ignored during a fallback scenario.",
        examples=[["max_latency_ms"]],
    )
    fallback_timeout_ms: int = Field(
        ...,
        description="The maximum time to wait in milliseconds while attempting to find a fallback routing solution.",
        examples=[10000],
    )
    allow_synthetic_bootstrapping: bool = Field(
        ...,
        description=(
            "If True, the orchestrator is allowed to synthetically generate a less optimal swarm to fulfill the intent."
        ),
        examples=[False],
    )


class UniversalIntentURI(CoreasonModel):
    """
    The core SOTA routing protocol for Universal Intent.
    Standardizes how macroscopic goals are mapped to isolated AI ecosystems
    (like local models or enterprise registries via MCP).
    """

    scheme: Literal["ibo", "mcp", "local"] = Field(
        ...,
        description="The routing scheme protocol to use for dispatching the intent.",
        examples=["ibo"],
    )
    ecosystem_target: str = Field(
        ...,
        description=(
            "The target registry, catalog, or provider where the intent should be resolved "
            "(e.g., 'huggingface', 'internal-registry')."
        ),
        examples=["internal-registry"],
    )
    semantic_payload: str = Field(
        ...,
        description="The dense natural language intent or macroscopic goal to be executed.",
        examples=["Extract temporal clinical relationships"],
    )
    constraints: ConstraintConfig = Field(
        ...,
        description="Hard execution boundaries ensuring compliance, latency, and regional data residency.",
    )
    degradation_policy: GracefulDegradationPolicy | None = Field(
        None,
        description="Optional policy detailing how the intent should degrade if the strict constraints cannot be met.",
    )
