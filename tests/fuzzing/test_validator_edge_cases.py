# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Hypothesis property tests covering uncovered validator error branches and edge cases."""

from typing import Any
from uuid import uuid4

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ConsensusFederationTopologyManifest,
    ContinuousMutationPolicy,
    CouncilTopologyManifest,
    GenerativeTaxonomyManifest,
    InterventionReceipt,
    PredictionMarketPolicy,
    QuorumPolicy,
    SystemNodeProfile,
    TaxonomicNodeState,
    WetwareAttestationContract,
)


def test_continuous_mutation_merge_on_resolve_allows_high_edges() -> None:
    """Prove that merge_on_resolve paradigm allows max_uncommitted_edges > 10000."""
    policy = ContinuousMutationPolicy(
        mutation_paradigm="merge_on_resolve",
        max_uncommitted_edges=50000,
        micro_batch_interval_ms=1000,
    )
    assert policy.max_uncommitted_edges == 50000


def test_generative_taxonomy_root_not_in_nodes() -> None:
    """Prove that GenerativeTaxonomyManifest rejects root_node_id not found in the matrix."""
    node = TaxonomicNodeState(node_id="existing_node", semantic_label="Existing Node")
    with pytest.raises(ValidationError, match="Topological Fracture"):
        GenerativeTaxonomyManifest(
            manifest_id="manifest_01",
            root_node_id="ghost_node",
            nodes={"existing_node": node},
        )


def test_generative_taxonomy_happy_path() -> None:
    """Prove that GenerativeTaxonomyManifest accepts root_node_id that exists in nodes."""
    node = TaxonomicNodeState(node_id="root_01", semantic_label="Root Node")
    manifest = GenerativeTaxonomyManifest(
        manifest_id="manifest_01",
        root_node_id="root_01",
        nodes={"root_01": node},
    )
    assert manifest.root_node_id == "root_01"


def test_intervention_receipt_attestation_nonce_mismatch() -> None:
    """Prove InterventionReceipt rejects WetwareAttestationContract with mismatched nonce."""
    request_id = uuid4()
    wrong_nonce = uuid4()

    attestation = WetwareAttestationContract(
        mechanism="fido2_webauthn",
        did_subject="did:web:human_operator",
        cryptographic_payload="AQID",
        dag_node_nonce=wrong_nonce,
    )

    with pytest.raises(ValidationError, match="Anti-Replay Lock Triggered"):
        InterventionReceipt(
            intervention_request_id=request_id,
            target_node_id="did:web:target",
            approved=True,
            feedback=None,
            attestation=attestation,
        )


def test_intervention_receipt_attestation_nonce_matches() -> None:
    """Prove InterventionReceipt accepts matching nonce in WetwareAttestationContract."""
    request_id = uuid4()

    attestation = WetwareAttestationContract(
        mechanism="fido2_webauthn",
        did_subject="did:web:human_operator",
        cryptographic_payload="AQID",
        dag_node_nonce=request_id,
    )

    receipt = InterventionReceipt(
        intervention_request_id=request_id,
        target_node_id="did:web:target",
        approved=True,
        feedback="Approved",
        attestation=attestation,
    )
    assert receipt.approved is True


def test_macro_grid_ghost_panel() -> None:
    """Prove MacroGridProfile rejects layout_matrix referencing non-existent panel IDs."""
    from coreason_manifest.spec.ontology import InsightCardProfile, MacroGridProfile

    panel = InsightCardProfile(
        panel_id="panel_1",
        title="Test",
        markdown_content="Hello World",
    )

    with pytest.raises(ValidationError, match="Ghost Panel"):
        MacroGridProfile(
            layout_matrix=[["panel_1", "panel_ghost"]],
            panels=[panel],
        )


@given(
    uncommitted=st.integers(min_value=10001, max_value=100000),
)
def test_continuous_mutation_append_only_bounds(uncommitted: int) -> None:
    """Prove that append_only paradigm with > 10000 uncommitted edges always triggers OOM bounding."""
    with pytest.raises(ValidationError, match="max_uncommitted_edges must be <= 10000"):
        ContinuousMutationPolicy(
            mutation_paradigm="append_only",
            max_uncommitted_edges=uncommitted,
            micro_batch_interval_ms=1000,
        )


def test_proposer_critique_topology_bipartite_validation() -> None:
    """Prove EvaluatorOptimizerTopologyManifest rejects ghost nodes and same generator/evaluator."""
    from coreason_manifest.spec.ontology import EvaluatorOptimizerTopologyManifest

    nodes: dict[str, Any] = {
        "did:web:gen": SystemNodeProfile(description="Generator"),
        "did:web:eval": SystemNodeProfile(description="Evaluator"),
    }

    # Ghost generator
    with pytest.raises(ValidationError, match="Generator node"):
        EvaluatorOptimizerTopologyManifest(
            nodes=nodes,
            generator_node_id="did:web:ghost",
            evaluator_node_id="did:web:eval",
            max_revision_loops=5,
        )

    # Ghost evaluator
    with pytest.raises(ValidationError, match="Evaluator node"):
        EvaluatorOptimizerTopologyManifest(
            nodes=nodes,
            generator_node_id="did:web:gen",
            evaluator_node_id="did:web:ghost",
            max_revision_loops=5,
        )

    # Same node for both
    with pytest.raises(ValidationError, match="Generator and Evaluator cannot be the same node"):
        EvaluatorOptimizerTopologyManifest(
            nodes=nodes,
            generator_node_id="did:web:gen",
            evaluator_node_id="did:web:gen",
            max_revision_loops=5,
        )


def test_evolutionary_topology_sorts_fitness_objectives() -> None:
    """Prove EvolutionaryTopologyManifest sorts fitness_objectives by target_metric."""
    from coreason_manifest.spec.ontology import (
        CrossoverPolicy,
        EvolutionaryTopologyManifest,
        FitnessObjectiveProfile,
        MutationPolicy,
    )

    obj_z = FitnessObjectiveProfile(target_metric="z_latency", direction="minimize")
    obj_a = FitnessObjectiveProfile(target_metric="a_accuracy", direction="maximize")

    nodes: dict[str, Any] = {"did:web:agent_1": SystemNodeProfile(description="Agent 1")}

    topo = EvolutionaryTopologyManifest(
        nodes=nodes,
        generations=1,
        population_size=10,
        mutation=MutationPolicy(mutation_rate=0.1, temperature_shift_variance=0.5),
        crossover=CrossoverPolicy(strategy_type="uniform_blend", blending_factor=0.5),
        fitness_objectives=[obj_z, obj_a],
    )
    assert topo.fitness_objectives[0].target_metric == "a_accuracy"
    assert topo.fitness_objectives[1].target_metric == "z_latency"


def test_adversarial_market_compile_to_base_topology() -> None:
    """Prove AdversarialMarketTopologyManifest compiles to a valid CouncilTopologyManifest."""
    from coreason_manifest.spec.ontology import AdversarialMarketTopologyManifest

    policy = PredictionMarketPolicy(
        staking_function="quadratic",
        min_liquidity_magnitude=100,
        convergence_delta_threshold=0.1,
    )

    manifest = AdversarialMarketTopologyManifest(
        blue_team_ids=["did:web:blue_1", "did:web:blue_2"],
        red_team_ids=["did:web:red_1"],
        adjudicator_id="did:web:adj",
        market_rules=policy,
    )

    compiled = manifest.compile_to_base_topology()
    assert isinstance(compiled, CouncilTopologyManifest)
    assert "did:web:adj" in compiled.nodes
    assert "did:web:blue_1" in compiled.nodes


def test_consensus_federation_compile_to_base_topology() -> None:
    """Prove ConsensusFederationTopologyManifest compiles to a valid CouncilTopologyManifest."""
    quorum = QuorumPolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="quarantine",
    )

    manifest = ConsensusFederationTopologyManifest(
        participant_ids=["did:web:p1", "did:web:p2", "did:web:p3"],
        adjudicator_id="did:web:adj",
        quorum_rules=quorum,
    )

    compiled = manifest.compile_to_base_topology()
    assert isinstance(compiled, CouncilTopologyManifest)
    assert "did:web:adj" in compiled.nodes
    assert "did:web:p1" in compiled.nodes


@given(
    depth=st.integers(min_value=6, max_value=10),
)
@settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
def test_agent_node_domain_extensions_depth_overflow(depth: int) -> None:
    """Prove AgentNodeProfile domain_extensions validator rejects excessive depth."""
    from coreason_manifest.spec.ontology import AgentNodeProfile

    payload: dict[str, Any] = {"leaf": "value"}
    for _ in range(depth):
        payload = {"nested": payload}

    with pytest.raises(ValidationError, match="maximum allowed depth"):
        AgentNodeProfile(
            description="test",
            domain_extensions=payload,
        )


def test_agent_node_domain_extensions_none_passthrough() -> None:
    """Prove AgentNodeProfile allows None for domain_extensions."""
    from coreason_manifest.spec.ontology import AgentNodeProfile

    node = AgentNodeProfile(description="test", domain_extensions=None)
    assert node.domain_extensions is None


def test_utility_justification_graph_interlocks() -> None:
    """Prove UtilityJustificationGraphReceipt rejects ensemble_spec with zero variance threshold."""
    from coreason_manifest.spec.ontology import (
        EnsembleTopologyProfile,
        UtilityJustificationGraphReceipt,
    )

    ensemble = EnsembleTopologyProfile(
        concurrent_branch_ids=["did:web:branch_1", "did:web:branch_2"],
        fusion_function="weighted_consensus",
    )

    with pytest.raises(ValidationError, match="Mathematical certainty prohibits superposition"):
        UtilityJustificationGraphReceipt(
            optimizing_vectors={"perf": 0.9},
            degrading_vectors={"cost": -0.1},
            superposition_variance_threshold=0.0,
            ensemble_spec=ensemble,
        )
