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
from typing import Annotated, ClassVar, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class ValidationRuleType(StrEnum):
    REQUIRED = "required"
    LENGTH = "length"
    RANGE = "range"
    REGEX = "regex"
    MATCH_FIELD = "match_field"
    CUSTOM_WEBHOOK = "custom_webhook"


class RuleRequired(CoreasonModel):
    rule_type: Literal[ValidationRuleType.REQUIRED] = ValidationRuleType.REQUIRED
    message: str


class RuleLength(CoreasonModel):
    rule_type: Literal[ValidationRuleType.LENGTH] = ValidationRuleType.LENGTH
    message: str
    min: int | None = None
    max: int | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> "RuleLength":
        """Enforce that at least one bound is provided and min is not greater than max."""
        if self.min is None and self.max is None:
            raise ValueError("At least one bound (min or max) must be provided.")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min cannot be greater than max.")
        return self


class RuleRange(CoreasonModel):
    rule_type: Literal[ValidationRuleType.RANGE] = ValidationRuleType.RANGE
    message: str
    min: float | None = None
    max: float | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> "RuleRange":
        """Enforce that at least one bound is provided and min is not greater than max."""
        if self.min is None and self.max is None:
            raise ValueError("At least one bound (min or max) must be provided.")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min cannot be greater than max.")
        return self


class RuleRegex(CoreasonModel):
    rule_type: Literal[ValidationRuleType.REGEX] = ValidationRuleType.REGEX
    message: str
    pattern: str


class RuleMatchField(CoreasonModel):
    rule_type: Literal[ValidationRuleType.MATCH_FIELD] = ValidationRuleType.MATCH_FIELD
    message: str
    target_field_id: str = Field(..., description="The ID of the field to match against (e.g., 'password_confirm').")


class RuleWebhook(CoreasonModel):
    rule_type: Literal[ValidationRuleType.CUSTOM_WEBHOOK] = ValidationRuleType.CUSTOM_WEBHOOK
    message: str
    url: str
    debounce_ms: int = Field(..., description="Debounce time in milliseconds before sending the validation request.")


ValidationRule = Annotated[
    RuleRequired | RuleLength | RuleRange | RuleRegex | RuleMatchField | RuleWebhook,
    Field(discriminator="rule_type"),
]


class UIValidationSchema(CoreasonModel):
    rules: list[ValidationRule]
    evaluate_on: Literal["change", "blur", "submit"] = "change"

    @model_validator(mode="after")
    def validate_rules(self) -> "UIValidationSchema":
        """Enforce that only one rule of specific types is allowed per schema."""
        rule_types_seen = set()
        for rule in self.rules:
            if rule.rule_type in (
                ValidationRuleType.REQUIRED,
                ValidationRuleType.LENGTH,
                ValidationRuleType.RANGE,
                ValidationRuleType.MATCH_FIELD,
            ):
                if rule.rule_type in rule_types_seen:
                    raise ValueError(f"Duplicate rule type found: {rule.rule_type}. Only one allowed per schema.")
                rule_types_seen.add(rule.rule_type)
        return self


class EpistemicValidator:
    """Validator for enforcing epistemic and ontological constraints."""

    EFFICACY_RELATIONS: ClassVar[set[str]] = {
        "treats",
        "cures",
        "increases survival",
        "decreases risk",
        "improves",
        "prevents",
    }

    @staticmethod
    def validate_statistical_grounding(
        relation: str, has_p_value: bool, has_confidence_interval: bool
    ) -> bool:
        """
        Enforce statistical grounding.

        If a relation implies efficacy, the claim must include a statistical marker
        (like p_value or confidence_interval).
        """
        return not (
            relation.lower() in EpistemicValidator.EFFICACY_RELATIONS
            and not has_p_value
            and not has_confidence_interval
        )
