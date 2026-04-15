# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Tests for Federated Discovery schemas introduced in the Federated Discovery epic."""

import time

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    FederatedDiscoveryIntent,
    OntologicalNormalizationIntent,
    OracleExecutionReceipt,
)

# ---------------------------------------------------------------------------
# §1. FederatedDiscoveryIntent
# ---------------------------------------------------------------------------


class TestFederatedDiscoveryIntent:
    """Validate FederatedDiscoveryIntent URN regex and Literal constraints."""

    def test_valid_construction(self) -> None:
        intent = FederatedDiscoveryIntent(
            domain_filter=["urn:coreason:domain:healthcare", "urn:coreason:domain:finance"],
            required_security_clearance="CONFIDENTIAL",
        )
        assert intent.topology_class == "federated_discovery"
        assert len(intent.domain_filter) == 2
        assert intent.required_security_clearance == "CONFIDENTIAL"
        # Verify cryptographic determinism: domain_filter must be sorted
        assert intent.domain_filter == ["urn:coreason:domain:finance", "urn:coreason:domain:healthcare"]

    def test_empty_domain_filter(self) -> None:
        intent = FederatedDiscoveryIntent(
            domain_filter=[],
            required_security_clearance="PUBLIC",
        )
        assert intent.domain_filter == []

    def test_invalid_domain_urn_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            FederatedDiscoveryIntent(
                domain_filter=["invalid-urn"],
                required_security_clearance="PUBLIC",
            )

    def test_non_coreason_urn_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            FederatedDiscoveryIntent(
                domain_filter=["urn:other:domain:test"],
                required_security_clearance="PUBLIC",
            )

    def test_invalid_security_clearance_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FederatedDiscoveryIntent(
                domain_filter=["urn:coreason:domain:test"],
                required_security_clearance="TOP_SECRET",  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize("clearance", ["PUBLIC", "CONFIDENTIAL", "RESTRICTED"])
    def test_all_valid_clearance_levels(self, clearance: str) -> None:
        intent = FederatedDiscoveryIntent(
            domain_filter=["urn:coreason:domain:test"],
            required_security_clearance=clearance,  # type: ignore[arg-type]
        )
        assert intent.required_security_clearance == clearance


# ---------------------------------------------------------------------------
# §2. OracleExecutionReceipt
# ---------------------------------------------------------------------------


class TestOracleExecutionReceipt:
    """Validate OracleExecutionReceipt URN regex, temporal constraints, and Merkle-DAG lineage."""

    def test_valid_construction(self) -> None:
        ts = time.time()
        receipt = OracleExecutionReceipt(
            event_cid="evt-oracle-001",
            timestamp=ts,
            executed_urn="urn:coreason:oracle:healthcare_etl",
            action_space_id="vpc-us-east-1-prod-001",
        )
        assert receipt.topology_class == "oracle_execution_receipt"
        assert receipt.timestamp == ts
        assert receipt.prior_event_hash is None

    def test_valid_construction_with_prior_hash(self) -> None:
        receipt = OracleExecutionReceipt(
            event_cid="evt-oracle-002",
            prior_event_hash="a" * 64,
            timestamp=1000.0,
            executed_urn="urn:coreason:oracle:finance_etl",
            action_space_id="vpc-001",
        )
        assert receipt.prior_event_hash == "a" * 64

    def test_invalid_prior_event_hash_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            OracleExecutionReceipt(
                event_cid="evt-oracle-003",
                prior_event_hash="not-a-sha256",
                timestamp=1000.0,
                executed_urn="urn:coreason:oracle:test",
                action_space_id="vpc-001",
            )

    def test_invalid_oracle_urn_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            OracleExecutionReceipt(
                event_cid="evt-001",
                executed_urn="not-a-urn",
                action_space_id="vpc-001",
                timestamp=1000.0,
            )

    def test_wrong_urn_namespace_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            OracleExecutionReceipt(
                event_cid="evt-001",
                executed_urn="urn:coreason:domain:wrong_namespace",
                action_space_id="vpc-001",
                timestamp=1000.0,
            )

    def test_invalid_action_space_id_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            OracleExecutionReceipt(
                event_cid="evt-001",
                executed_urn="urn:coreason:oracle:test",
                action_space_id="invalid space id!",
                timestamp=1000.0,
            )

    def test_negative_timestamp_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OracleExecutionReceipt(
                event_cid="evt-001",
                executed_urn="urn:coreason:oracle:test",
                action_space_id="vpc-001",
                timestamp=-1.0,
            )


# ---------------------------------------------------------------------------
# §3. OntologicalNormalizationIntent
# ---------------------------------------------------------------------------


class TestOntologicalNormalizationIntent:
    """Validate OntologicalNormalizationIntent URN regex and CID constraints."""

    def test_valid_construction(self) -> None:
        intent = OntologicalNormalizationIntent(
            source_artifact_cid="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
            target_ontology_urn="urn:coreason:ontology:omop_cdm_v5",
        )
        assert intent.topology_class == "ontological_normalization"

    def test_invalid_ontology_urn_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            OntologicalNormalizationIntent(
                source_artifact_cid="valid-cid-123",
                target_ontology_urn="not-a-valid-urn",
            )

    def test_wrong_ontology_urn_namespace_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            OntologicalNormalizationIntent(
                source_artifact_cid="valid-cid-123",
                target_ontology_urn="urn:coreason:oracle:wrong_type",
            )

    def test_empty_source_cid_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OntologicalNormalizationIntent(
                source_artifact_cid="",
                target_ontology_urn="urn:coreason:ontology:test",
            )

    def test_source_cid_special_chars_rejected(self) -> None:
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            OntologicalNormalizationIntent(
                source_artifact_cid="invalid cid with spaces!",
                target_ontology_urn="urn:coreason:ontology:test",
            )
