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

from coreason_manifest.spec.v2.constitution import (
    Constitution,
    Law,
    LawCategory,
    LawSeverity,
    SentinelRule,
)
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.provenance import ProvenanceData
from coreason_manifest.spec.v2.recipe import (
    GraphTopology,
    HumanNode,
    PolicyConfig,
    RecipeDefinition,
    RecipeInterface,
)


def test_complex_full_integration() -> None:
    """Test full Recipe with complex PolicyConfig + Constitution."""
    # 1. Create a detailed Constitution
    laws = [
        Law(
            id=f"LAW.{i}",
            category=LawCategory.UNIVERSAL if i % 2 == 0 else LawCategory.DOMAIN,
            text=f"Rule number {i}",
            severity=LawSeverity.CRITICAL if i == 0 else LawSeverity.MEDIUM,
        )
        for i in range(10)
    ]
    sentinels = [SentinelRule(id="S1", pattern="[0-9]+", description="Block numbers")]
    const = Constitution(laws=laws, sentinel_rules=sentinels)

    # 2. Integrate into PolicyConfig
    policy = PolicyConfig(
        max_retries=5,
        timeout_seconds=3600,
        execution_mode="parallel",
        safety_preamble="Legacy Safety Check",  # Should coexist
        constitution=const,
    )

    # 3. Create full Recipe
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(
            name="Compliance Recipe",
            description="A recipe with strict governance.",
            version="1.0.0",
            provenance=ProvenanceData(type="human", generated_by="admin"),
        ),
        interface=RecipeInterface(inputs={}, outputs={}),
        policy=policy,
        topology=GraphTopology(
            entry_point="start",
            nodes=[HumanNode(id="start", prompt="Hi")],
            edges=[],
        ),
    )

    # 4. Verify round-trip serialization
    json_str = recipe.to_json()
    assert '"LAW.0"' in json_str
    assert '"LAW.9"' in json_str
    assert '"Legacy Safety Check"' in json_str
    assert '"constitution"' in json_str

    # 5. Verify deserialization
    reloaded = RecipeDefinition.model_validate_json(json_str)
    assert reloaded.policy is not None
    assert reloaded.policy.constitution is not None
    assert len(reloaded.policy.constitution.laws) == 10
    assert reloaded.policy.safety_preamble == "Legacy Safety Check"


def test_large_volume_laws() -> None:
    """Test creating a Constitution with a large number of laws."""
    num_laws = 1000
    laws = [Law(id=f"L.{i}", text=f"Text {i}") for i in range(num_laws)]

    const = Constitution(laws=laws)
    assert len(const.laws) == num_laws

    # Verify JSON serialization performance/validity
    json_str = const.to_json()
    assert f'"id":"L.{num_laws - 1}"' in json_str


def test_nested_immutability() -> None:
    """Test immutability deep within the structure."""
    const = Constitution(laws=[Law(id="L1", text="Immutable")])
    policy = PolicyConfig(constitution=const)

    # Pydantic V2 raises ValidationError for frozen instances
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        policy.constitution.laws = []  # type: ignore
