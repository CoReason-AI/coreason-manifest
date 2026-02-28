# Prosperity-3.0
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.common_base import CoreasonModel
from coreason_manifest.core.compliance import RemediationAction
from coreason_manifest.core.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.core.oversight.resilience import EscalationStrategy
from coreason_manifest.core.primitives.registry import register_node
from coreason_manifest.core.primitives.types import VariableID

from .base import Node


class SteeringConfig(CoreasonModel):
    """
    Configuration for human steering permissions.
    """

    allow_variable_mutation: bool = Field(False, description="Whether the human can mutate blackboard variables.")
    allowed_targets: list[VariableID] | None = Field(
        None, description="List of variable IDs that can be mutated. If None, all are allowed (if mutation is enabled)."
    )

    @model_validator(mode="after")
    def validate_mutation_permissions(self) -> "SteeringConfig":
        if not self.allow_variable_mutation and self.allowed_targets is not None:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_HUMAN_STEERING,
                message="SteeringConfig defines 'allowed_targets' but 'allow_variable_mutation' is False.",
                context={
                    "remediation": RemediationAction(
                        type="update_field",
                        description="Enable mutation or remove targets.",
                        patch_data=[{"op": "remove", "path": "/allowed_targets"}],
                    ).model_dump()
                },
            )
        if self.allow_variable_mutation and self.allowed_targets is not None and len(self.allowed_targets) == 0:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_HUMAN_STEERING,
                message="allowed_targets cannot be empty when mutation is allowed. Use None to allow all targets.",
                context={
                    "remediation": RemediationAction(
                        type="update_field",
                        description="Set allowed_targets to None or populate it.",
                        patch_data=[{"op": "replace", "path": "/allowed_targets", "value": None}],
                    ).model_dump()
                },
            )
        return self


@register_node
class HumanNode(Node):
    """
    Human-in-the-Loop interaction node.
    Supports blocking approval, or 'shadow' mode where the agent streams intent
    and proceeds if no signal is received, while 'hijack_only' allows mid-flight plan alteration.
    """

    type: Literal["human"] = "human"
    prompt: str = Field(..., description="Prompt to display to the human.", examples=["Approve this plan?"])
    escalation: EscalationStrategy = Field(..., description="The escalation configuration.")
    input_schema: dict[str, Any] | None = Field(
        None, description="JSON Schema for expected human input.", examples=[{"type": "object"}]
    )
    options: list[str] | None = Field(
        None, description="List of valid options for the human.", examples=[["approve", "reject"]]
    )

    interaction_mode: Annotated[
        Literal["blocking", "shadow", "hijack_only"],
        Field(description="Wait for input vs shadow execution.", examples=["blocking"]),
    ] = "blocking"

    steering_config: SteeringConfig | None = Field(None, description="Configuration for steering permissions.")

    @model_validator(mode="after")
    def validate_interaction_mode(self) -> "HumanNode":
        if self.interaction_mode == "shadow" and (self.input_schema is not None or self.options is not None):
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_HUMAN_SHADOW,
                message="HumanNode in 'shadow' mode cannot have 'input_schema' or 'options'.",
                context={
                    "remediation": RemediationAction(
                        type="update_field",
                        target_node_id=self.id,
                        description="Remove 'input_schema' and 'options'.",
                        patch_data=[
                            {"op": "remove", "path": "/input_schema"},
                            {"op": "remove", "path": "/options"},
                        ],
                    ).model_dump()
                },
            )
        if self.interaction_mode == "hijack_only" and self.steering_config is None:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_HUMAN_STEERING,
                message="HumanNode in 'hijack_only' mode requires 'steering_config'.",
                context={
                    "remediation": RemediationAction(
                        type="update_field",
                        target_node_id=self.id,
                        description="Add 'steering_config'.",
                        patch_data=[
                            {
                                "op": "add",
                                "path": "/steering_config",
                                "value": {"allow_variable_mutation": True},
                            }
                        ],
                    ).model_dump()
                },
            )
        return self
