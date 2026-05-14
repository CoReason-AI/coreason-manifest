# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for CognitiveStateProfile, SemanticSlicing, routing contracts, and HOTL configuration."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    InterventionPolicy,
    SpatialHardwareProfile,
    SpatialOntologicalSurfaceProjectionManifest,
)


class TestSpatialHardwareProfile:
    """Exercise canonical sort of provider_whitelist."""

    def test_provider_whitelist_sorted(self) -> None:
        obj = SpatialHardwareProfile(
            provider_whitelist=["gcp", "aws", "azure", "vast"],
        )
        assert obj.provider_whitelist == sorted(obj.provider_whitelist)

    @given(
        providers=st.lists(
            st.text(alphabet="abcdefghij", min_size=1, max_size=5),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=15, deadline=None)
    def test_provider_whitelist_always_sorted(self, providers: list[str]) -> None:
        obj = SpatialHardwareProfile(provider_whitelist=providers)
        assert obj.provider_whitelist == sorted(providers)


class TestInterventionPolicy:
    """Exercise validate_hotl_configuration validator."""

    def test_valid_blocking_policy(self) -> None:
        obj = InterventionPolicy(trigger="on_start")
        assert obj.blocking is True

    def test_telemetry_without_port_rejected(self) -> None:
        with pytest.raises(ValidationError, match="async_observation_port"):
            InterventionPolicy(
                trigger="on_failure",
                blocking=False,
                emit_telemetry_on_revision=True,
            )

    def test_telemetry_with_port_valid(self) -> None:
        obj = InterventionPolicy(
            trigger="on_failure",
            blocking=False,
            emit_telemetry_on_revision=True,
            async_observation_port="https://telemetry.example.com",  # type: ignore[arg-type]
        )
        assert obj.emit_telemetry_on_revision is True

    def test_non_blocking_without_telemetry_valid(self) -> None:
        obj = InterventionPolicy(
            trigger="on_failure",
            blocking=False,
            emit_telemetry_on_revision=False,
        )
        assert obj.emit_telemetry_on_revision is False


class TestOntologicalSurfaceProjectionManifest:
    """Exercise structural uniqueness and canonical sort validators."""

    def test_empty_projection(self) -> None:
        obj = SpatialOntologicalSurfaceProjectionManifest(projection_cid="proj-1")
        assert obj.action_spaces == []
        assert obj.supported_personas == []
