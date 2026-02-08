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
from coreason_manifest.spec.v2.recipe import PolicyConfig


def test_law_instantiation() -> None:
    """Test creating a Law object."""
    law = Law(
        id="GCP.4",
        category=LawCategory.DOMAIN,
        text="Do not harm humans.",
        severity=LawSeverity.CRITICAL,
        reference_url="https://example.com/gcp4",
    )

    assert law.id == "GCP.4"
    assert law.category == LawCategory.DOMAIN
    assert law.text == "Do not harm humans."
    assert law.severity == LawSeverity.CRITICAL
    assert law.reference_url == "https://example.com/gcp4"


def test_law_defaults() -> None:
    """Test default values for Law."""
    law = Law(
        id="TEST.1",
        text="Simple rule.",
    )

    assert law.category == LawCategory.DOMAIN
    assert law.severity == LawSeverity.MEDIUM
    assert law.reference_url is None


def test_sentinel_rule_instantiation() -> None:
    """Test creating a SentinelRule object."""
    rule = SentinelRule(
        id="SR-001",
        pattern=r"sk-[a-zA-Z0-9]{48}",
        description="Block OpenAI API keys.",
    )

    assert rule.id == "SR-001"
    assert rule.pattern == r"sk-[a-zA-Z0-9]{48}"
    assert rule.description == "Block OpenAI API keys."


def test_constitution_assembly() -> None:
    """Test assembling a Constitution with Laws and SentinelRules."""
    law1 = Law(id="L1", text="Rule 1")
    law2 = Law(id="L2", text="Rule 2", severity=LawSeverity.HIGH)
    rule1 = SentinelRule(id="S1", pattern="bad", description="No bad")

    const = Constitution(laws=[law1, law2], sentinel_rules=[rule1])

    assert len(const.laws) == 2
    assert len(const.sentinel_rules) == 1
    assert const.laws[0].id == "L1"
    assert const.sentinel_rules[0].id == "S1"


def test_policy_config_integration() -> None:
    """Test integrating Constitution into PolicyConfig."""
    const = Constitution(
        laws=[Law(id="L1", text="Be nice")],
        sentinel_rules=[SentinelRule(id="S1", pattern="hate", description="No hate")],
    )

    policy = PolicyConfig(
        max_retries=3,
        constitution=const,
    )

    assert policy.max_retries == 3
    assert policy.constitution is not None
    assert len(policy.constitution.laws) == 1
    assert policy.constitution.laws[0].text == "Be nice"


def test_policy_config_serialization() -> None:
    """Test JSON serialization of PolicyConfig with Constitution."""
    const = Constitution(
        laws=[Law(id="L1", text="Be nice")],
    )
    policy = PolicyConfig(constitution=const)

    json_output = policy.to_json()
    # model_dump_json produces compact JSON (no spaces after separators)
    assert '"id":"L1"' in json_output
    assert '"text":"Be nice"' in json_output
    assert '"constitution"' in json_output


def test_immutability() -> None:
    """Test that models are frozen."""
    law = Law(id="L1", text="Immutable")
    with pytest.raises(ValidationError):
        law.text = "Changed"  # type: ignore

    const = Constitution()
    with pytest.raises(ValidationError):
        const.laws = []  # type: ignore
