from typing import Literal

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.resilience import EscalationStrategy

InterventionMode = Literal["blocking", "shadow", "hijack_only"]


class EscalationCriteria(CoreasonModel):
    """
    Defines conditions under which an agent should escalate to a human.
    """

    condition: str = Field(
        ...,
        description="Python expression string (AST-whitelisted) to evaluate against agent state.",
        examples=["risk_level == 'CRITICAL'", "confidence < 0.85"],
    )
    role: str = Field(
        ...,
        description="The human role required to handle this escalation.",
        examples=["supervisor", "legal_compliance"],
    )
    priority: Literal["low", "medium", "high", "critical"] = "medium"


class CoIntelligencePolicy(CoreasonModel):
    """
    Global policy for Human-AI Co-Intelligence.
    """

    global_intervention_mode: InterventionMode = Field(
        "blocking",
        description="Default intervention mode for the entire flow.",
    )
    escalation_rules: list[EscalationCriteria] = Field(
        default_factory=list,
        description="Global list of conditions that trigger escalation.",
    )
    default_sla: EscalationStrategy | None = Field(
        None,
        description="Default escalation strategy for global interventions.",
    )
