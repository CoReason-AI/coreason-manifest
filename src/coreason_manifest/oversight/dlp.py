# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:
This file maps the Data Loss Prevention (DLP) and Semantic Firewall schemas. This is a STRICTLY REGULATORY BOUNDARY.
These schemas define the Zero-Trust information flow constraints of the swarm.
DO NOT inject kinetic execution logic here.
All policies must be declarative, deterministic, and capable of severing memory access instantly.
"""

from typing import Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.compute.neuromodulation import SaeLatentFirewall
from coreason_manifest.core.base import CoreasonBaseModel

type DataClassification = Literal["phi", "pii", "pci", "confidential", "public"]
type SanitizationAction = Literal["redact", "hash", "drop_event", "trigger_quarantine"]


class RedactionRule(CoreasonBaseModel):
    """
    A specific rule for algorithmic data sanitization.
    """

    rule_id: str = Field(description="Unique identifier for the sanitization rule.")
    classification: DataClassification = Field(description="The category of sensitive data this rule targets.")
    target_pattern: str = Field(description="The semantic entity type or declarative regex pattern to identify.")
    target_regex_pattern: str = Field(max_length=200, description="The dynamic regex pattern to target.")
    context_exclusion_zones: list[str] | None = Field(
        default=None, max_length=100, description="Specific JSON paths where this rule should NOT apply."
    )
    action: SanitizationAction = Field(description="The required algorithmic response when this pattern is detected.")
    replacement_token: str | None = Field(
        default=None, description="The strictly typed string to insert if the action is 'redact'."
    )


class SecureSubSession(CoreasonBaseModel):
    """
    Declarative boundary for handling unredacted secrets within a temporarily isolated memory partition.
    """

    session_id: str = Field(max_length=255, description="Unique identifier for the secure session.")
    allowed_vault_keys: list[str] = Field(
        max_length=100, description="List of enterprise vault keys the agent is temporarily allowed to access."
    )
    max_ttl_seconds: int = Field(ge=1, le=3600, description="Maximum time-to-live for the unredacted memory partition.")
    description: str = Field(max_length=2000, description="Audit justification for this temporary secure session.")


class SemanticFirewallPolicy(CoreasonBaseModel):
    max_input_tokens: int = Field(
        gt=0, description="The absolute physical ceiling of tokens allowed in a single ingress payload."
    )
    forbidden_intents: list[str] = Field(
        default_factory=list,
        description=(
            "A strict list of semantic intents (e.g., 'role_override', "
            "'system_prompt_leak') that trigger immediate quarantine."
        ),
    )
    action_on_violation: Literal["drop", "quarantine", "redact"] = Field(
        description="The deterministic action the orchestrator must take if a firewall rule is violated."
    )


class InformationFlowPolicy(CoreasonBaseModel):
    """
    Mathematical Data Loss Prevention (DLP) contract that bounds the graph.
    """

    policy_id: str = Field(description="Unique identifier for this macroscopic flow control policy.")
    active: bool = Field(default=True, description="Whether this policy is currently enforcing data sanitization.")
    rules: list[RedactionRule] = Field(default_factory=list, description="The array of sanitization rules to enforce.")
    semantic_firewall: SemanticFirewallPolicy | None = Field(
        default=None,
        description="The active cognitive defense perimeter against adversarial control-flow overrides.",
    )
    latent_firewalls: list[SaeLatentFirewall] = Field(
        default_factory=list,
        description=(
            "The list of tensor-level mechanistic firewalls monitoring the forward pass for adversarial intent."
        ),
    )

    @model_validator(mode="after")
    def sort_rules(self) -> Self:
        """
        Mathematically sorts rules by rule_id to guarantee deterministic hashing.
        """
        # Because the model is frozen, we bypass attribute assignment tracking
        object.__setattr__(self, "rules", sorted(self.rules, key=lambda r: r.rule_id))
        return self
