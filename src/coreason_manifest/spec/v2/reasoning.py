from enum import StrEnum

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel


class ReviewStrategy(StrEnum):
    """How the node output is critiqued."""

    NONE = "none"
    BASIC = "basic"  # Simple self-correction
    ADVERSARIAL = "adversarial"  # Devil's Advocate persona
    CAUSAL = "causal"  # Check logical consistency/fallacies
    CONSENSUS = "consensus"  # Multi-model agreement (Harvested from Council)


class AdversarialConfig(CoReasonBaseModel):
    """Configuration for the 'Devil's Advocate' reviewer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    persona: str = Field(
        "skeptic",
        description="The persona adopted by the reviewer (e.g., 'security_auditor', 'skeptic').",
    )
    attack_vectors: list[str] = Field(
        default_factory=list,
        description="Specific angles of critique (e.g., 'pii_leakage', 'hallucination').",
    )
    temperature: float = Field(0.7, description="Creativity level of the critique.")


class GapScanConfig(CoReasonBaseModel):
    """Configuration for Knowledge Gap detection (Episteme)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = Field(
        False, description="If True, scans context for missing prerequisites before execution."
    )
    confidence_threshold: float = Field(
        0.8,
        description="Minimum confidence to proceed without asking clarifying questions.",
    )


class ReasoningConfig(CoReasonBaseModel):
    """Container for meta-cognitive behaviors attached to a Node."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy: ReviewStrategy = Field(
        ReviewStrategy.NONE,
        description="The active critique method applied to this node's output.",
    )

    # Strategy-specific configs
    adversarial: AdversarialConfig | None = Field(
        None, description="Config if strategy is ADVERSARIAL."
    )
    gap_scan: GapScanConfig | None = Field(
        None, description="Config for pre-execution knowledge scanning."
    )

    max_revisions: int = Field(
        1, description="Maximum self-correction loops allowed if critique fails."
    )
