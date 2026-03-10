# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    BilateralSLA,
    CrossSwarmHandshakeState,
    FederatedDiscoveryManifest,
    InformationClassification,
)


def test_federated_discovery_protocol_valid() -> None:
    """Test valid instantiation of FederatedDiscoveryManifest."""
    protocol = FederatedDiscoveryManifest(
        broadcast_endpoints=["mcp://swarm.tenant-a.com/bidding", "mcp://backup.tenant-a.com/bidding"],
        supported_ontologies=["sha256:1234567890abcdef", "sha256:0987654321fedcba"],
    )
    assert len(protocol.broadcast_endpoints) == 2
    assert len(protocol.supported_ontologies) == 2


def test_federated_discovery_protocol_missing_fields() -> None:
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        FederatedDiscoveryManifest()  # type: ignore

    errors = exc_info.value.errors()
    missing_fields = [err["loc"][0] for err in errors if err["type"] == "missing"]
    assert "broadcast_endpoints" in missing_fields
    assert "supported_ontologies" in missing_fields


def test_cross_swarm_handshake_valid() -> None:
    """Test valid instantiation of CrossSwarmHandshakeState."""
    sla = BilateralSLA(
        receiving_tenant_id="did:example:tenant-b",
        max_permitted_classification=InformationClassification.RESTRICTED,
        liability_limit_magnitude=1000000,
        permitted_geographic_regions=["us-east-1", "eu-west-1"],
    )

    handshake = CrossSwarmHandshakeState(
        handshake_id="handshake-001",
        initiating_tenant_id="did:example:tenant-a",
        receiving_tenant_id="did:example:tenant-b",
        offered_sla=sla,
        status="proposed",
    )

    assert handshake.handshake_id == "handshake-001"
    assert handshake.initiating_tenant_id == "did:example:tenant-a"
    assert handshake.status == "proposed"
    assert handshake.offered_sla.liability_limit_magnitude == 1000000


def test_cross_swarm_handshake_default_status() -> None:
    """Test that the default status is 'proposed'."""
    sla = BilateralSLA(
        receiving_tenant_id="did:example:tenant-b",
        max_permitted_classification=InformationClassification.PUBLIC,
        liability_limit_magnitude=0,
    )

    handshake = CrossSwarmHandshakeState(
        handshake_id="handshake-002",
        initiating_tenant_id="did:example:tenant-a",
        receiving_tenant_id="did:example:tenant-b",
        offered_sla=sla,
    )

    assert handshake.status == "proposed"


def test_cross_swarm_handshake_invalid_status() -> None:
    """Test that an invalid status raises ValidationError."""
    sla = BilateralSLA(
        receiving_tenant_id="did:example:tenant-b",
        max_permitted_classification=InformationClassification.PUBLIC,
        liability_limit_magnitude=0,
    )

    with pytest.raises(ValidationError) as exc_info:
        CrossSwarmHandshakeState(
            handshake_id="handshake-003",
            initiating_tenant_id="did:example:tenant-a",
            receiving_tenant_id="did:example:tenant-b",
            offered_sla=sla,
            status="pending",  # type: ignore
        )

    errors = exc_info.value.errors()
    assert any(err["loc"] == ("status",) for err in errors)
    assert any("literal_error" in err["type"] or "value_error" in err["type"] for err in errors)


def test_cross_swarm_handshake_missing_fields() -> None:
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CrossSwarmHandshakeState()  # type: ignore

    errors = exc_info.value.errors()
    missing_fields = [err["loc"][0] for err in errors if err["type"] == "missing"]
    assert "handshake_id" in missing_fields
    assert "initiating_tenant_id" in missing_fields
    assert "receiving_tenant_id" in missing_fields
    assert "offered_sla" in missing_fields
