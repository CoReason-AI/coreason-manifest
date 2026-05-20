# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CommercialOverrideReceipt,
    DAGTopologyManifest,
    EnsembleTopologyProfile,
    StateDifferentialManifest,
)


class TestCommercialOverrideReceipt:
    """Verify CommercialOverrideReceipt behavior, JWT fallback mappings, and bounds."""

    def test_jwt_claims_fallback(self) -> None:
        # Create without exp/iat, verify before validator maps them correctly
        # We use model_validate to test the dynamic before-validator without triggering Mypy errors
        receipt = CommercialOverrideReceipt.model_validate(
            {
                "license_tier": "commercial",
                "signer_did": "did:key:zmocksignerkey",
                "signature_algorithm": "ML-DSA-65",
                "credential_format": "sd-jwt",
                "distr_license_cid": "license-123",
                "issued_at_epoch": 1000,
                "expires_at_epoch": 2000,
                "entitlements": ["COMMERCIAL_USE"],
                "network_mode": "private",
                "federation_enabled": False,
            }
        )
        assert receipt.exp == 2000
        assert receipt.iat == 1000

    def test_jwt_claims_consistency_check(self) -> None:
        # Test exp mismatched with expires_at_epoch raises validation error
        with pytest.raises(ValidationError, match=r"exp .* must match expires_at_epoch"):
            CommercialOverrideReceipt.model_validate(
                {
                    "license_tier": "commercial",
                    "signer_did": "did:key:zmocksignerkey",
                    "signature_algorithm": "ML-DSA-65",
                    "credential_format": "sd-jwt",
                    "distr_license_cid": "license-123",
                    "issued_at_epoch": 1000,
                    "expires_at_epoch": 2000,
                    "exp": 9999,  # Mismatched
                    "iat": 1000,
                    "entitlements": ["COMMERCIAL_USE"],
                    "network_mode": "private",
                    "federation_enabled": False,
                }
            )

    def test_entitlements_max_length_bound(self) -> None:
        # 1001 items exceeds max_length=1000 limit
        large_entitlements = ["FLAG"] * 1001
        with pytest.raises(ValidationError, match="List should have at most 1000 items"):
            CommercialOverrideReceipt(
                license_tier="commercial",
                signer_did="did:key:zmocksignerkey",
                signature_algorithm="ML-DSA-65",
                credential_format="sd-jwt",
                distr_license_cid="license-123",
                issued_at_epoch=1000,
                expires_at_epoch=2000,
                exp=2000,
                iat=1000,
                entitlements=large_entitlements,
                network_mode="private",
                federation_enabled=False,
            )


class TestMemoryBounds:
    """Verify max_length constraints enforce array bounds at validation time."""

    def test_crdt_patches_bounds(self) -> None:
        from coreason_manifest.spec.ontology import StateMutationIntent

        large_patches = [
            StateMutationIntent(
                op="add",
                path="/foo/bar",
                value="test",
            )
        ] * 1001
        with pytest.raises(ValidationError, match="List should have at most 1000 items"):
            StateDifferentialManifest(
                diff_cid="diff-1",
                author_node_cid="did:key:zmockauthornode",
                lamport_timestamp=1,
                vector_clock={},
                patches=large_patches,
            )

    def test_dag_topology_manifest_edges_bounds(self) -> None:
        large_edges = [("did:key:zmockauthornode", "did:key:zmockauthornode")] * 10001
        with pytest.raises(ValidationError, match="List should have at most 10000 items"):
            DAGTopologyManifest(
                nodes={},
                edges=large_edges,
                max_depth=10,
                max_fan_out=5,
            )

    def test_ensemble_topology_branch_bounds(self) -> None:
        # ensemble branches limit is 100
        large_branches = ["did:key:zmockauthornode"] * 101
        with pytest.raises(ValidationError, match="List should have at most 100 items"):
            EnsembleTopologyProfile(
                concurrent_branch_cids=large_branches,
                fusion_function="weighted_consensus",
            )
