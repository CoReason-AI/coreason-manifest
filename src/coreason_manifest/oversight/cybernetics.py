from pydantic import BaseModel, ConfigDict, Field, model_validator

from coreason_manifest.oversight.intervention import AnyInterventionPayload
from coreason_manifest.oversight.resilience import AnyResiliencePayload


class CyberneticControlLoop(BaseModel):
    """
    AGENT INSTRUCTION: This struct represents a HOLOGRAPHIC RECEIPT of a cybernetic
    control calculation (Sensor -> Controller -> Actuator). It is mathematically
    flattened. Do NOT instantiate active monitoring loops. Downstream engines read
    this state to execute physical interventions.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    homeostatic_deviation_vector: dict[str, int | float | str | bool] = Field(
        ..., description="Deterministic JSON-primitive dictionary representing the topological or tensor drift."
    )

    adjudication_rationale: str = Field(
        ..., description="The deterministic reasoning output of the Governor or rules-engine."
    )

    regulatory_intervention_action: AnyResiliencePayload | AnyInterventionPayload = Field(
        ..., description="The declarative actuation boundary guaranteeing structurally legal interventions."
    )

    @model_validator(mode="after")
    def _enforce_intervention_bounds(self) -> "CyberneticControlLoop":
        # Mathematical constraint: Severe deviations must map to severe interventions.
        deviation = self.homeostatic_deviation_vector
        action = self.regulatory_intervention_action

        if deviation.get("byzantine_fault_detected") is True:
            # We enforce that the action must be a severe resilience payload,
            # represented here by asserting the schema type or specific intent.
            # (Assuming NetworkQuarantineIntent exists in AnyResiliencePayload)
            action_type = getattr(action, "intent", None)
            if action_type not in ("QUARANTINE", "SLASH_STAKE", "CIRCUIT_BREAK"):
                raise ValueError(
                    "ECONOMICS_VIOLATION: A Byzantine fault requires a severe regulatory intervention "
                    "(QUARANTINE, SLASH_STAKE, or CIRCUIT_BREAK)."
                )
        return self
