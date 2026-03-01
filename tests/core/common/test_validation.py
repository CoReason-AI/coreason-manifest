# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.core.common.validation import (
    RuleLength,
    RuleMatchField,
    RuleRange,
    RuleRegex,
    RuleRequired,
    RuleWebhook,
    UIValidationSchema,
    ValidationRuleType,
)


def test_rule_required() -> None:
    rule = RuleRequired(message="Field is required")
    assert rule.rule_type == ValidationRuleType.REQUIRED
    assert rule.message == "Field is required"


def test_rule_length_valid() -> None:
    rule1 = RuleLength(message="Min length 5", min=5)
    assert rule1.min == 5
    assert rule1.max is None

    rule2 = RuleLength(message="Max length 10", max=10)
    assert rule2.min is None
    assert rule2.max == 10

    rule3 = RuleLength(message="Length 5-10", min=5, max=10)
    assert rule3.min == 5
    assert rule3.max == 10


def test_rule_length_invalid() -> None:
    with pytest.raises(ValidationError, match="At least one bound"):
        RuleLength(message="Invalid")

    with pytest.raises(ValidationError, match="min cannot be greater than max"):
        RuleLength(message="Invalid", min=10, max=5)


def test_rule_range_valid() -> None:
    rule1 = RuleRange(message="Min range 5.0", min=5.0)
    assert rule1.min == 5.0
    assert rule1.max is None

    rule2 = RuleRange(message="Max range 10.0", max=10.0)
    assert rule2.min is None
    assert rule2.max == 10.0

    rule3 = RuleRange(message="Range 5.0-10.0", min=5.0, max=10.0)
    assert rule3.min == 5.0
    assert rule3.max == 10.0


def test_rule_range_invalid() -> None:
    with pytest.raises(ValidationError, match="At least one bound"):
        RuleRange(message="Invalid")

    with pytest.raises(ValidationError, match="min cannot be greater than max"):
        RuleRange(message="Invalid", min=10.0, max=5.0)


def test_rule_regex() -> None:
    rule = RuleRegex(message="Must be alphanumeric", pattern="^[a-zA-Z0-9]+$")
    assert rule.rule_type == ValidationRuleType.REGEX
    assert rule.pattern == "^[a-zA-Z0-9]+$"


def test_rule_match_field() -> None:
    rule = RuleMatchField(message="Passwords must match", target_field_id="password")
    assert rule.rule_type == ValidationRuleType.MATCH_FIELD
    assert rule.target_field_id == "password"


def test_rule_webhook() -> None:
    rule = RuleWebhook(message="Checking username...", url="https://api.example.com/check", debounce_ms=500)
    assert rule.rule_type == ValidationRuleType.CUSTOM_WEBHOOK
    assert rule.url == "https://api.example.com/check"
    assert rule.debounce_ms == 500


def test_ui_validation_schema_valid() -> None:
    schema = UIValidationSchema(
        rules=[
            RuleRequired(message="Required"),
            RuleLength(message="Length", min=5),
            RuleRegex(message="Regex 1", pattern="^foo$"),
            RuleRegex(message="Regex 2", pattern="^bar$"),
            RuleWebhook(message="Webhook 1", url="http://1", debounce_ms=100),
            RuleWebhook(message="Webhook 2", url="http://2", debounce_ms=100),
        ],
        evaluate_on="blur",
    )
    assert len(schema.rules) == 6
    assert schema.evaluate_on == "blur"


def test_ui_validation_schema_duplicate_type_contradiction() -> None:
    with pytest.raises(ValidationError, match="Duplicate rule type found: length"):
        UIValidationSchema(
            rules=[
                RuleLength(message="Length 1", min=5),
                RuleLength(message="Length 2", max=10),
            ]
        )

    with pytest.raises(ValidationError, match="Duplicate rule type found: range"):
        UIValidationSchema(
            rules=[
                RuleRange(message="Range 1", min=5.0),
                RuleRange(message="Range 2", max=10.0),
            ]
        )

    with pytest.raises(ValidationError, match="Duplicate rule type found: required"):
        UIValidationSchema(
            rules=[
                RuleRequired(message="Required 1"),
                RuleRequired(message="Required 2"),
            ]
        )

    with pytest.raises(ValidationError, match="Duplicate rule type found: match_field"):
        UIValidationSchema(
            rules=[
                RuleMatchField(message="Match 1", target_field_id="field1"),
                RuleMatchField(message="Match 2", target_field_id="field2"),
            ]
        )
