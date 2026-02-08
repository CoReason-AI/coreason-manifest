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

from coreason_manifest.spec.v2.constitution import (
    Constitution,
    Law,
    LawCategory,
    LawSeverity,
    SentinelRule,
)


def test_law_validation_failures() -> None:
    """Test that Law validation fails for invalid inputs."""
    # 1. Empty ID
    with pytest.raises(ValidationError) as exc:
        Law(id="", text="Valid text")  # type: ignore
    assert "String should have at least 1 character" in str(exc.value)

    # 2. Empty Text
    with pytest.raises(ValidationError) as exc:
        Law(id="L1", text="")  # type: ignore
    assert "String should have at least 1 character" in str(exc.value)

    # 3. Missing Required Fields
    with pytest.raises(ValidationError):
        Law(id="L1")  # type: ignore[call-arg]


def test_optional_fields_none() -> None:
    """Test explicit None for optional fields."""
    law = Law(
        id="L1",
        text="Text",
        reference_url=None,
    )
    assert law.reference_url is None

    # Verify defaults are applied even if not passed
    assert law.category == LawCategory.DOMAIN
    assert law.severity == LawSeverity.MEDIUM


def test_extreme_inputs() -> None:
    """Test extremely long strings to ensure no arbitrary limits (unless defined)."""
    long_text = "A" * 10000
    law = Law(id="L_LONG", text=long_text)
    assert len(law.text) == 10000
    assert law.text == long_text


def test_empty_lists() -> None:
    """Test empty lists for laws and sentinel_rules."""
    const = Constitution(laws=[], sentinel_rules=[])
    assert len(const.laws) == 0
    assert len(const.sentinel_rules) == 0

    # Default factory checks
    const_default = Constitution()
    assert const_default.laws == []
    assert const_default.sentinel_rules == []


def test_duplicate_ids_allowed() -> None:
    """
    Test that duplicate IDs are currently allowed by the schema.
    If uniqueness enforcement is added later, this test should be updated to expect failure.
    """
    law1 = Law(id="L1", text="Rule A")
    law2 = Law(id="L1", text="Rule B")  # Same ID

    const = Constitution(laws=[law1, law2])
    assert len(const.laws) == 2
    assert const.laws[0].id == "L1"
    assert const.laws[1].id == "L1"


def test_sentinel_rule_validation() -> None:
    """Test SentinelRule validation edge cases."""
    # Missing pattern
    with pytest.raises(ValidationError):
        SentinelRule(id="S1", description="Desc")  # type: ignore[call-arg]

    # Empty strings (should ideally fail if min_length was set, checking behavior)
    # The current schema doesn't set min_length for SentinelRule fields, so this might pass.
    # Let's verify standard behavior.
    rule = SentinelRule(id="", pattern="", description="")
    assert rule.id == ""
    assert rule.pattern == ""


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError) as exc:
        Law(id="L1", text="T", extra_field="bad")  # type: ignore[call-arg]
    assert "Extra inputs are not permitted" in str(exc.value)
