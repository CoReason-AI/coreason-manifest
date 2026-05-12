# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for FederatedBilateralSLA, EphemeralNamespacePartitionState, and security-layer models."""

import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    EphemeralNamespacePartitionState,
    FederatedBilateralSLA,
    FederatedCapabilityAttestationReceipt,
    FederatedSecurityMacroManifest,
    SecureSubSessionState,
    SemanticClassificationProfile,
)

# ---------------------------------------------------------------------------
# EphemeralNamespacePartitionState
# ---------------------------------------------------------------------------


VALID_HASH = "a" * 64
INVALID_HASH = "ZZZZ"


class TestEphemeralNamespacePartitionState:
    """Exercise SHA-256 hash validation and canonical sort."""

    def _make(self, **overrides) -> EphemeralNamespacePartitionState:  # type: ignore[no-untyped-def]
        defaults = {
            "partition_cid": "p-1",
            "execution_runtime": "wasm32-wasi",
            "authorized_bytecode_hashes": [VALID_HASH],
            "max_ttl_seconds": 60,
            "max_vram_mb": 512,
        }
        defaults.update(overrides)
        return EphemeralNamespacePartitionState(**defaults)  # type: ignore[arg-type]

    def test_valid_partition(self) -> None:
        obj = self._make()
        assert obj.allow_network_egress is False
        assert obj.allow_subprocess_spawning is False

    def test_invalid_hash_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Invalid SHA-256"):
            self._make(authorized_bytecode_hashes=[INVALID_HASH])

    def test_multiple_valid_hashes_sorted(self) -> None:
        h1 = "b" * 64
        h2 = "a" * 64
        obj = self._make(authorized_bytecode_hashes=[h1, h2])
        assert obj.authorized_bytecode_hashes == sorted([h1, h2])

    def test_mixed_valid_invalid_hash_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Invalid SHA-256"):
            self._make(authorized_bytecode_hashes=[VALID_HASH, "notahash"])

    @given(
        hex_chars=st.text(alphabet="0123456789abcdef", min_size=64, max_size=64),
    )
    @settings(max_examples=15, deadline=None)
    def test_valid_sha256_always_accepted(self, hex_chars: str) -> None:
        obj = self._make(authorized_bytecode_hashes=[hex_chars])
        assert len(obj.authorized_bytecode_hashes) == 1
        assert re.match("^[a-f0-9]{64}$", obj.authorized_bytecode_hashes[0])


# ---------------------------------------------------------------------------
# FederatedBilateralSLA
# ---------------------------------------------------------------------------


class TestFederatedBilateralSLA:
    """Test basic construction and classification usage."""

    def test_valid_sla(self) -> None:
        sla = FederatedBilateralSLA(
            receiving_tenant_cid="tenant-1",
            max_permitted_classification=SemanticClassificationProfile.INTERNAL,
            liability_limit_magnitude=1000,
            permitted_geographic_regions=["us-east-1", "eu-west-1"],
        )
        assert sla.max_permitted_classification == SemanticClassificationProfile.INTERNAL

    def test_geographic_regions_sorted(self) -> None:
        sla = FederatedBilateralSLA(
            receiving_tenant_cid="tenant-2",
            max_permitted_classification=SemanticClassificationProfile.PUBLIC,
            liability_limit_magnitude=500,
            permitted_geographic_regions=["eu-west-1", "ap-south-1", "us-east-1"],
        )
        assert sla.permitted_geographic_regions == sorted(sla.permitted_geographic_regions)


# ---------------------------------------------------------------------------
# FederatedCapabilityAttestationReceipt — restricted vault lock
# ---------------------------------------------------------------------------


class TestFederatedCapabilityAttestationReceipt:
    """Exercise enforce_restricted_vault_locks validator."""

    def test_restricted_without_vault_keys_rejected(self) -> None:
        sla = FederatedBilateralSLA(
            receiving_tenant_cid="tenant-1",
            max_permitted_classification=SemanticClassificationProfile.RESTRICTED,
            liability_limit_magnitude=1000,
            permitted_geographic_regions=[],
        )
        session = SecureSubSessionState(
            session_cid="ss-1",
            allowed_vault_keys=[],
            max_ttl_seconds=3600,
            description="test session",
        )
        with pytest.raises(ValidationError, match="RESTRICTED"):
            FederatedCapabilityAttestationReceipt(
                attestation_cid="att-1",
                target_topology_cid="did:z:target-1",
                authorized_session=session,
                governing_sla=sla,
            )

    def test_restricted_with_vault_keys_valid(self) -> None:
        sla = FederatedBilateralSLA(
            receiving_tenant_cid="tenant-1",
            max_permitted_classification=SemanticClassificationProfile.RESTRICTED,
            liability_limit_magnitude=1000,
            permitted_geographic_regions=[],
        )
        session = SecureSubSessionState(
            session_cid="ss-1",
            allowed_vault_keys=["key-1"],
            max_ttl_seconds=3600,
            description="test session",
        )
        obj = FederatedCapabilityAttestationReceipt(
            attestation_cid="att-1",
            target_topology_cid="did:z:target-1",
            authorized_session=session,
            governing_sla=sla,
        )
        assert obj.governing_sla.max_permitted_classification == SemanticClassificationProfile.RESTRICTED

    def test_non_restricted_without_vault_keys_valid(self) -> None:
        sla = FederatedBilateralSLA(
            receiving_tenant_cid="tenant-1",
            max_permitted_classification=SemanticClassificationProfile.INTERNAL,
            liability_limit_magnitude=1000,
            permitted_geographic_regions=[],
        )
        session = SecureSubSessionState(
            session_cid="ss-1",
            allowed_vault_keys=[],
            max_ttl_seconds=3600,
            description="test session",
        )
        obj = FederatedCapabilityAttestationReceipt(
            attestation_cid="att-1",
            target_topology_cid="did:z:target-1",
            authorized_session=session,
            governing_sla=sla,
        )
        assert obj.governing_sla.max_permitted_classification == SemanticClassificationProfile.INTERNAL


# ---------------------------------------------------------------------------
# FederatedSecurityMacroManifest
# ---------------------------------------------------------------------------


class TestFederatedSecurityMacroManifest:
    """Exercise compile_to_base_topology macro method."""

    def test_compile_to_base(self) -> None:
        macro = FederatedSecurityMacroManifest(
            target_endpoint_uri="api.example.com",
            required_clearance=SemanticClassificationProfile.CONFIDENTIAL,
            max_liability_budget=5000,
        )
        sla = macro.compile_to_base_topology()
        assert isinstance(sla, FederatedBilateralSLA)
        assert sla.max_permitted_classification == SemanticClassificationProfile.CONFIDENTIAL
        assert sla.liability_limit_magnitude == 5000
