# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any

from coreason_manifest.spec.ontology import (
    CognitiveSwarmDeploymentManifest,
    FederatedSecurityMacroManifest,
    SemanticClassificationProfile,
    _inject_cognitive_routing_cluster,
    _inject_dag_examples_and_routing_cluster,
    _inject_diff_examples_and_epistemic_cluster,
    _inject_epistemic_cluster,
    _inject_security_cluster,
    _inject_sim_examples_and_security_cluster,
    _inject_spatial_cluster,
    _inject_thermodynamic_cluster,
    _inject_workflow_examples_and_routing_cluster,
)


def test_federated_security_macro() -> None:
    macro = FederatedSecurityMacroManifest(
        target_endpoint_uri="did:target.com",
        required_clearance=SemanticClassificationProfile.PUBLIC,
        max_liability_budget=100,
    )
    topology = macro.compile_to_base_topology()
    assert topology.receiving_tenant_cid == "did:target.com"
    assert topology.max_permitted_classification == SemanticClassificationProfile.PUBLIC
    assert topology.liability_limit_magnitude == 100


def test_cognitive_swarm_deployment_macro_majority() -> None:
    macro = CognitiveSwarmDeploymentManifest(
        swarm_objective_prompt="Solve puzzle", agent_node_count=3, consensus_mechanism="majority"
    )
    topology = macro.compile_to_base_topology()
    assert len(topology.nodes) == 4
    assert topology.adjudicator_cid == "did:coreason:adjudicator"
    assert topology.consensus_policy is not None
    assert topology.consensus_policy.strategy == "majority"


def test_cognitive_swarm_deployment_macro_pbft() -> None:
    macro = CognitiveSwarmDeploymentManifest(
        swarm_objective_prompt="Solve puzzle", agent_node_count=3, consensus_mechanism="pbft"
    )
    topology = macro.compile_to_base_topology()
    assert len(topology.nodes) == 4
    assert topology.consensus_policy is not None
    assert topology.consensus_policy.strategy == "pbft"


def test_cognitive_swarm_deployment_macro_prediction_market() -> None:
    macro = CognitiveSwarmDeploymentManifest(
        swarm_objective_prompt="Solve puzzle", agent_node_count=3, consensus_mechanism="prediction_market"
    )
    topology = macro.compile_to_base_topology()
    assert len(topology.nodes) == 4
    assert topology.consensus_policy is not None
    assert topology.consensus_policy.strategy == "prediction_market"


def test_injectors() -> None:
    schema: dict[str, Any] = {}
    _inject_spatial_cluster(schema)
    assert schema["x-domain-cluster"] == "spatial_kinematics"

    schema = {}
    _inject_epistemic_cluster(schema)
    assert schema["x-domain-cluster"] == "epistemic_ledger"

    schema = {}
    _inject_cognitive_routing_cluster(schema)
    assert schema["x-domain-cluster"] == "cognitive_routing"

    schema = {}
    _inject_thermodynamic_cluster(schema)
    assert schema["x-domain-cluster"] == "thermodynamic_orchestration"

    schema = {}
    _inject_security_cluster(schema)
    assert schema["x-domain-cluster"] == "zero_trust_security"

    schema = {}
    _inject_diff_examples_and_epistemic_cluster(schema)
    assert schema["x-domain-cluster"] == "epistemic_ledger"
    assert "examples" in schema

    schema = {}
    _inject_sim_examples_and_security_cluster(schema)
    assert schema["x-domain-cluster"] == "zero_trust_security"
    assert "examples" in schema

    schema = {}
    _inject_dag_examples_and_routing_cluster(schema)
    assert schema["x-domain-cluster"] == "cognitive_routing"
    assert "examples" in schema

    schema = {}
    _inject_workflow_examples_and_routing_cluster(schema)
    assert schema["x-domain-cluster"] == "cognitive_routing"
    assert "examples" in schema
