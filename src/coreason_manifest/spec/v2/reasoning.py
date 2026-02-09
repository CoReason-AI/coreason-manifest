# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import StrEnum

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import ManifestBaseModel


class ReviewStrategy(StrEnum):
    """How the node output is critiqued."""

    NONE = "none"
    BASIC = "basic"  # Simple self-correction
    ADVERSARIAL = "adversarial"  # Devil's Advocate persona
    CAUSAL = "causal"  # Check logical consistency/fallacies
    CONSENSUS = "consensus"  # Multi-model agreement


class AdversarialConfig(ManifestBaseModel):
    """
    Configuration for the 'Devil's Advocate' reviewer.

    Attributes:
        persona (str): The persona adopted by the reviewer (e.g., 'security_auditor', 'skeptic'). (Default: "skeptic").
        attack_vectors (list[str]): Specific angles of critique (e.g., 'pii_leakage', 'hallucination').
        temperature (float): Creativity level of the critique. (Default: 0.7).
    """

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


class GapScanConfig(ManifestBaseModel):
    """
    Configuration for Knowledge Gap detection (Episteme).

    Attributes:
        enabled (bool): If True, scans context for missing prerequisites before execution. (Default: False).
        confidence_threshold (float): Minimum confidence to proceed without asking clarifying questions. (Default: 0.8).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = Field(False, description="If True, scans context for missing prerequisites before execution.")
    confidence_threshold: float = Field(
        0.8,
        description="Minimum confidence to proceed without asking clarifying questions.",
    )


class ReasoningConfig(ManifestBaseModel):
    """
    Container for meta-cognitive behaviors attached to a Node.

    Attributes:
        strategy (ReviewStrategy): The active critique method applied to this node's output. (Default: NONE).
        adversarial (AdversarialConfig | None): Config if strategy is ADVERSARIAL.
        gap_scan (GapScanConfig | None): Config for pre-execution knowledge scanning.
        max_revisions (int): Maximum self-correction loops allowed if critique fails. (Default: 1).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy: ReviewStrategy = Field(
        ReviewStrategy.NONE,
        description="The active critique method applied to this node's output.",
    )

    # Strategy-specific configs
    adversarial: AdversarialConfig | None = Field(None, description="Config if strategy is ADVERSARIAL.")
    gap_scan: GapScanConfig | None = Field(None, description="Config for pre-execution knowledge scanning.")

    max_revisions: int = Field(1, description="Maximum self-correction loops allowed if critique fails.")


class ReflexConfig(ManifestBaseModel):
    """
    Configuration for 'System 1' fast thinking (Cortex Reflex).

    Attributes:
        enabled (bool): Allow fast-path responses without deep reasoning chains. (Default: True).
        confidence_threshold (float): Minimum confidence required to bypass the solver loop. (Default: 0.9).
        allowed_tools (list[str]): List of read-only tools that can be called in Reflex mode (e.g., 'search',
            'get_time').
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = Field(True, description="Allow fast-path responses without deep reasoning chains.")
    confidence_threshold: float = Field(0.9, description="Minimum confidence required to bypass the solver loop.")
    allowed_tools: list[str] = Field(
        default_factory=list,
        description="List of read-only tools that can be called in Reflex mode (e.g., 'search', 'get_time').",
    )
