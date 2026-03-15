# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Hypothesis property tests proving deterministic canonical sorting of model_validator paths."""

import hypothesis.strategies as st
from hypothesis import HealthCheck, given, settings

from coreason_manifest.spec.ontology import (
    AgentAttestationReceipt,
    AgentBidIntent,
    AuctionState,
    ConsensusFederationTopologyManifest,
    ConstitutionalPolicy,
    EpistemicAxiomState,
    EpistemicDomainGraphManifest,
    EpistemicProvenanceReceipt,
    GovernancePolicy,
    MCPClientBindingProfile,
    MechanisticAuditContract,
    NeuralAuditAttestationReceipt,
    QuorumPolicy,
    SaeFeatureActivationState,
    TaskAnnouncementIntent,
    TaxonomicNodeState,
    VerifiableCredentialPresentationReceipt,
)


@given(
    rule_ids=st.lists(
        st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True).filter(lambda x: 1 <= len(x) <= 128),
        min_size=2,
        max_size=5,
        unique=True,
    )
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_governance_policy_sorts_rules(rule_ids: list[str]) -> None:
    """Prove GovernancePolicy deterministically sorts its rules by rule_id."""
    rules = [
        ConstitutionalPolicy(rule_id=rid, severity="low", description="test", forbidden_intents=[]) for rid in rule_ids
    ]
    policy = GovernancePolicy(
        policy_name="test_policy",
        version="1.0.0",
        rules=rules,
    )
    assert [r.rule_id for r in policy.rules] == sorted(rule_ids)


@given(
    children=st.lists(
        st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True).filter(lambda x: 1 <= len(x) <= 128),
        min_size=2,
        max_size=5,
        unique=True,
    )
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_taxonomic_node_sorts_children(children: list[str]) -> None:
    """Prove TaxonomicNodeState deterministically sorts children_node_ids and leaf_provenance."""
    prov_a = EpistemicProvenanceReceipt(extracted_by="did:web:node_a", source_event_id="evt_z")
    prov_b = EpistemicProvenanceReceipt(extracted_by="did:web:node_b", source_event_id="evt_a")

    node = TaxonomicNodeState(
        node_id="node_1",
        semantic_label="Test Node",
        children_node_ids=children,
        leaf_provenance=[prov_a, prov_b],
    )
    assert node.children_node_ids == sorted(children)
    assert node.leaf_provenance[0].source_event_id == "evt_a"


@given(
    trigger_conditions=st.lists(
        st.sampled_from(["on_tool_call", "on_belief_mutation", "on_quarantine", "on_falsification"]),
        min_size=2,
        max_size=4,
        unique=True,
    ),
    target_layers=st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=5, unique=True),
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_mechanistic_audit_sorts_arrays(trigger_conditions: list[str], target_layers: list[int]) -> None:
    """Prove MechanisticAuditContract deterministically sorts trigger_conditions and target_layers."""
    contract = MechanisticAuditContract(
        trigger_conditions=trigger_conditions,
        target_layers=target_layers,
        max_features_per_layer=100,
    )
    assert contract.trigger_conditions == sorted(trigger_conditions)
    assert contract.target_layers == sorted(target_layers)


def test_neural_audit_attestation_sorts_layer_activations() -> None:
    """Prove NeuralAuditAttestationReceipt sorts layer_activations by feature_index."""
    feat_z = SaeFeatureActivationState(feature_index=99, activation_magnitude=0.9, interpretability_label="Z-feature")
    feat_a = SaeFeatureActivationState(feature_index=1, activation_magnitude=0.5, interpretability_label="A-feature")

    receipt = NeuralAuditAttestationReceipt(
        audit_id="audit_01",
        layer_activations={0: [feat_z, feat_a]},
    )
    assert receipt.layer_activations[0][0].feature_index == 1
    assert receipt.layer_activations[0][1].feature_index == 99


@given(
    agent_ids=st.lists(
        st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True).filter(lambda x: 1 <= len(x) <= 128),
        min_size=2,
        max_size=4,
        unique=True,
    )
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_auction_state_sorts_bids(agent_ids: list[str]) -> None:
    """Prove AuctionState deterministically sorts bids by agent_id."""
    bids = [
        AgentBidIntent(
            agent_id=aid,
            estimated_cost_magnitude=100,
            estimated_latency_ms=100,
            estimated_carbon_gco2eq=0.1,
            confidence_score=0.9,
        )
        for aid in agent_ids
    ]
    announcement = TaskAnnouncementIntent(
        task_id="task_1",
        required_action_space_id=None,
        max_budget_magnitude=1000,
    )
    state = AuctionState(
        announcement=announcement,
        bids=bids,
        clearing_timeout=5000,
        minimum_tick_size=1.0,
    )
    assert [b.agent_id for b in state.bids] == sorted(agent_ids)


@given(
    issuer_dids=st.lists(
        st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True),
        min_size=2,
        max_size=4,
        unique=True,
    )
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_agent_attestation_sorts_credential_presentations(issuer_dids: list[str]) -> None:
    """Prove AgentAttestationReceipt deterministically sorts credential_presentations by issuer_did."""
    credentials = [
        VerifiableCredentialPresentationReceipt(
            presentation_format="jwt_vc",
            issuer_did=did,
            cryptographic_proof_blob="proof_hash_123",
            authorization_claims={},
        )
        for did in issuer_dids
    ]
    receipt = AgentAttestationReceipt(
        training_lineage_hash="a" * 64,
        developer_signature="sig_abc",
        capability_merkle_root="b" * 64,
        credential_presentations=credentials,
    )
    assert [c.issuer_did for c in receipt.credential_presentations] == sorted(issuer_dids)


def test_epistemic_domain_graph_sorts_axioms() -> None:
    """Prove EpistemicDomainGraphManifest sorts verified_axioms by multi-key sort."""
    ax_z = EpistemicAxiomState(
        source_concept_id="concept_Z",
        directed_edge_type="is_a",
        target_concept_id="concept_A",
    )
    ax_a = EpistemicAxiomState(
        source_concept_id="concept_A",
        directed_edge_type="part_of",
        target_concept_id="concept_B",
    )

    graph = EpistemicDomainGraphManifest(
        graph_id="graph_01",
        verified_axioms=[ax_z, ax_a],
    )
    assert graph.verified_axioms[0].source_concept_id == "concept_A"
    assert graph.verified_axioms[1].source_concept_id == "concept_Z"


@given(
    participant_ids=st.lists(
        st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True),
        min_size=3,
        max_size=6,
        unique=True,
    ),
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_consensus_federation_sorts_participants(participant_ids: list[str]) -> None:
    """Prove ConsensusFederationTopologyManifest sorts participant_ids and rejects adjudicator in participants."""
    import pytest
    from pydantic import ValidationError

    adj = "did:web:adjudicator_node"

    from hypothesis import assume

    assume(adj not in participant_ids)

    quorum = QuorumPolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="quarantine",
    )

    manifest = ConsensusFederationTopologyManifest(
        participant_ids=participant_ids,
        adjudicator_id=adj,
        quorum_rules=quorum,
    )
    assert manifest.participant_ids == sorted(participant_ids)

    # Also prove adjudicator isolation rejection
    with pytest.raises(ValidationError, match="Topological Contradiction"):
        ConsensusFederationTopologyManifest(
            participant_ids=[adj, participant_ids[0], participant_ids[1]],
            adjudicator_id=adj,
            quorum_rules=quorum,
        )


def test_mcp_client_binding_sorts_allowed_tools() -> None:
    """Prove MCPClientBindingProfile sorts allowed_mcp_tools when present."""
    binding = MCPClientBindingProfile(
        server_uri="stdio://test",
        transport_type="stdio",
        allowed_mcp_tools=["z_tool", "a_tool", "m_tool"],
    )
    assert binding.allowed_mcp_tools == ["a_tool", "m_tool", "z_tool"]

    # Also prove None path is valid
    binding_none = MCPClientBindingProfile(
        server_uri="stdio://test",
        transport_type="stdio",
        allowed_mcp_tools=None,
    )
    assert binding_none.allowed_mcp_tools is None
