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
from coreason_manifest.definitions.agent import ModelConfig, Persona
from coreason_manifest.definitions.simulation_config import AdversaryProfile
from pydantic import ValidationError


def test_persona_empty_strings() -> None:
    """Test Persona instantiation with empty strings (allowed by Pydantic but worth checking behavior)."""
    persona = Persona(name="", description="", directives=[])
    assert persona.name == ""
    assert persona.description == ""
    assert persona.directives == []


def test_persona_missing_fields() -> None:
    """Test Persona validation failure when required fields are missing."""
    with pytest.raises(ValidationError):
        Persona(name="Just Name")  # type: ignore[call-arg]


def test_model_config_with_system_prompt_and_persona() -> None:
    """Test that ModelConfig accepts both system_prompt and persona."""
    persona = Persona(name="Test", description="Test Desc", directives=["Act normal"])
    config = ModelConfig(
        model="gpt-4",
        temperature=0.5,
        system_prompt="Global prompt",
        persona=persona,
    )
    assert config.system_prompt == "Global prompt"
    assert config.persona == persona
    assert config.persona.name == "Test"


def test_adversary_profile_optional_persona() -> None:
    """Test backward compatibility: AdversaryProfile without persona."""
    profile = AdversaryProfile(
        name="Old Profile",
        goal="Legacy goal",
        strategy_model="gpt-3.5",
        attack_model="gpt-3.5",
    )
    assert profile.persona is None


def test_adversary_profile_with_empty_directives_persona() -> None:
    """Test AdversaryProfile with a Persona having empty directives."""
    persona = Persona(name="Lazy Adversary", description="Does nothing", directives=[])
    profile = AdversaryProfile(
        name="Lazy Profile",
        goal="Do nothing",
        strategy_model="gpt-4",
        attack_model="gpt-4",
        persona=persona,
    )
    assert profile.persona is not None
    assert len(profile.persona.directives) == 0
