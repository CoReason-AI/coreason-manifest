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
    CapabilityForgeTopologyManifest,
    CognitiveAgentNodeProfile,
    CognitiveHumanNodeProfile,
    HumanDirectiveIntent,
    IntentElicitationTopologyManifest,
    SemanticDiscoveryIntent,
    VectorEmbeddingState,
)


def test_human_directive_intent_valid() -> None:
    intent = HumanDirectiveIntent(
        natural_language_goal="Build a stock scraper.", allocated_budget_magnitude=1000, target_qos="interactive"
    )
    assert intent.topology_class== "human_directive"
    assert intent.natural_language_goal == "Build a stock scraper."
    assert intent.allocated_budget_magnitude == 1000
    assert intent.target_qos == "interactive"


def test_human_directive_intent_budget_exceeds() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HumanDirectiveIntent(
            natural_language_goal="Solve AGI.", allocated_budget_magnitude=1000000001, target_qos="interactive"
        )
    assert "allocated_budget_magnitude" in str(exc_info.value)
    assert "Input should be less than or equal to 1000000000" in str(exc_info.value)


def get_dummy_deficit() -> SemanticDiscoveryIntent:
    return SemanticDiscoveryIntent(
        query_vector=VectorEmbeddingState(vector_base64="eQ==", dimensionality=1, foundation_matrix_name="test_model"),
        min_isometry_score=0.5,
        required_structural_types=["type1"],
    )


def test_capability_forge_topology_manifest_without_human_supervisor() -> None:
    manifest = CapabilityForgeTopologyManifest(
        target_epistemic_deficit=get_dummy_deficit(),
        generator_node_cid="did:coreason:agent-gen",
        formal_verifier_cid="did:coreason:sys-ver",
        fuzzing_engine_cid="did:coreason:sys-fuzz",
        nodes={},
    )
    dag = manifest.compile_to_base_topology()
    assert len(dag.nodes) == 3
    assert len(dag.edges) == 2
    assert ("did:coreason:agent-gen", "did:coreason:sys-ver") in dag.edges
    assert ("did:coreason:sys-ver", "did:coreason:sys-fuzz") in dag.edges


def test_capability_forge_topology_manifest_with_human_supervisor() -> None:
    manifest = CapabilityForgeTopologyManifest(
        target_epistemic_deficit=get_dummy_deficit(),
        generator_node_cid="did:coreason:agent-gen",
        formal_verifier_cid="did:coreason:sys-ver",
        fuzzing_engine_cid="did:coreason:sys-fuzz",
        human_supervisor_cid="did:coreason:human-1",
        nodes={},
    )
    dag = manifest.compile_to_base_topology()
    assert len(dag.nodes) == 4
    assert len(dag.edges) == 3
    assert ("did:coreason:sys-fuzz", "did:coreason:human-1") in dag.edges
    assert "did:coreason:human-1" in dag.nodes
    human_node = dag.nodes["did:coreason:human-1"]
    assert isinstance(human_node, CognitiveHumanNodeProfile)
    assert human_node.description == "Forge HITL Supervisor"
    assert human_node.required_attestation == "fido2_webauthn"


def test_intent_elicitation_macro_compilation() -> None:
    manifest = IntentElicitationTopologyManifest(
        raw_human_artifact_cid="test_artifact_1",
        transmuter_node_cid="did:coreason:sys-transmuter",
        scanner_node_cid="did:coreason:agent-scanner",
        human_oracle_cid="did:coreason:human-oracle",
        nodes={},
    )
    dag = manifest.compile_to_base_topology()

    assert len(dag.nodes) == 3
    assert len(dag.edges) == 3
    assert ("did:coreason:sys-transmuter", "did:coreason:agent-scanner") in dag.edges
    assert ("did:coreason:agent-scanner", "did:coreason:human-oracle") in dag.edges
    assert ("did:coreason:human-oracle", "did:coreason:agent-scanner") in dag.edges

    assert dag.allow_cycles is True

    scanner_node = dag.nodes["did:coreason:agent-scanner"]
    assert isinstance(scanner_node, CognitiveAgentNodeProfile)
    assert scanner_node.epistemic_policy is not None
    assert scanner_node.epistemic_policy.action_on_gap == "clarify"
