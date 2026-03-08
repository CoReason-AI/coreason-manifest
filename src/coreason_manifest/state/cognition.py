# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable cognitive schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
monotonic logic, standard CRUD database paradigms, or kinetic execution parameters. These models represent computable
geometric graphs of cognition and causal inference."""

from pydantic import Field

from coreason_manifest.compute.neuromodulation import ActivationSteeringContract, CognitiveRoutingDirective
from coreason_manifest.core.base import CoreasonBaseModel


class CognitiveUncertaintyProfile(CoreasonBaseModel):
    """Structural Causal Models (SCMs) for active epistemic bounding."""
    aleatoric_entropy: float = Field(
        ge=0.0, le=1.0, description="Irreducible ambiguity detected in the observational fields (P(y|x))."
    )
    epistemic_uncertainty: float = Field(
        ge=0.0, le=1.0, description="The causal gap demanding Do-Calculus Interventions (P(y|do(x)))."
    )
    semantic_consistency_score: float = Field(
        ge=0.0, le=1.0, description="Counterfactual Geometries representing alternative timeline vectors."
    )
    requires_abductive_escalation: bool = Field(
        description="True if epistemic_uncertainty breaches the safety threshold, requiring structural mandate "
        "escalation."
    )


class CognitiveStateProfile(CoreasonBaseModel):
    """Causal Directed Acyclic Graphs (cDAGs) and constraints for state progression."""
    urgency_index: float = Field(
        ge=0.0, le=1.0, description="Drives structural constraints; high urgency forces fast heuristic routing."
    )
    caution_index: float = Field(
        ge=0.0, le=1.0, description="Drives precision; high caution injects analytical/falsification steering vectors."
    )
    divergence_tolerance: float = Field(
        ge=0.0,
        le=1.0,
        description="The 'curiosity' metric; dictates how far the router is allowed to stray "
        "from high-probability distributions.",
    )
    activation_steering: ActivationSteeringContract | None = Field(
        default=None,
        description="The precise mathematical contract for altering the residual stream to enforce this constraint.",
    )
    moe_routing_directive: CognitiveRoutingDirective | None = Field(
        default=None,
        description="The structural mandate overriding default token routing to "
        "enforce this cognitive state.",
    )
