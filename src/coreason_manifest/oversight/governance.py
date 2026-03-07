# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID, SemanticVersion


class ConstitutionalRule(CoreasonBaseModel):
    """
    Defines a constitutional rule for AI governance.
    """

    rule_id: str = Field(description="Unique identifier for the constitutional rule.")
    description: str = Field(description="Detailed description of the rule.")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Severity level if the rule is violated."
    )
    forbidden_intents: set[Annotated[str, StringConstraints(min_length=1)]] = Field(
        description="List of intents that are forbidden by this rule."
    )


class GovernancePolicy(CoreasonBaseModel):
    """
    Defines a governance policy comprising multiple constitutional rules.
    """

    policy_name: str = Field(description="Name of the governance policy.")
    version: SemanticVersion = Field(description="Semantic version of the governance policy.")
    rules: list[ConstitutionalRule] = Field(description="List of constitutional rules included in this policy.")


class ConsensusPolicy(CoreasonBaseModel):
    """
    Explicit ruleset governing how a council resolves disagreements.
    """

    strategy: Literal["unanimous", "majority", "debate_rounds"] = Field(
        description="The mathematical rule for reaching agreement."
    )
    tie_breaker_node_id: NodeID | None = Field(
        default=None, description="The node authorized to break deadlocks if unanimity or majority fails."
    )
    max_debate_rounds: int | None = Field(
        default=None,
        description="The maximum number of argument/rebuttal cycles permitted before forced adjudication.",
    )


class FormalVerificationContract(CoreasonBaseModel):
    """
    Passive schema defining a mathematical proof of safety invariants.
    """

    proof_system: Literal["tla_plus", "lean4", "coq", "z3"] = Field(
        description="The mathematical dialect and theorem prover used to compile the proof."
    )
    invariant_theorem: str = Field(
        description=(
            "The exact mathematical assertion or safety invariant being proven "
            "(e.g., 'No data classified as CONFIDENTIAL routes externally')."
        )
    )
    compiled_proof_hash: str = Field(
        description=(
            "The SHA-256 fingerprint of the verified proof object that the Rust/C++ orchestrator must load and check."
        )
    )


class GlobalGovernance(CoreasonBaseModel):
    """
    Global governance bounds for a swarm executing a workflow envelope.
    """

    max_budget_cents: int = Field(
        description="The absolute maximum economic cost allowed for the entire swarm lifecycle."
    )
    max_global_tokens: int = Field(description="The maximum aggregate token usage allowed across all nodes.")
    global_timeout_seconds: int = Field(
        ge=0, description="The absolute Time-To-Live (TTL) for the execution envelope before graceful termination."
    )
    formal_verification: FormalVerificationContract | None = Field(
        default=None,
        description="The mathematical proof of structural correctness mandated for this execution graph.",
    )
