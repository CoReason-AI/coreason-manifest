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
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CognitiveSystemNodeProfile,
    CrossoverPolicy,
    DAGTopologyManifest,
    DerivationModeProfile,
    EpistemicProvenanceReceipt,
    EvaluatorOptimizerTopologyManifest,
    EvolutionaryTopologyManifest,
    FederatedBilateralSLA,
    FitnessObjectiveProfile,
    MutationPolicy,
    RiskLevelPolicy,
    SemanticClassificationProfile,
    SMPCTopologyManifest,
    WorkflowManifest,
)


@given(st.sampled_from(list(SemanticClassificationProfile)), st.sampled_from(list(SemanticClassificationProfile)))
def test_information_classification_profile_comparisons(
    prof1: SemanticClassificationProfile, prof2: SemanticClassificationProfile
) -> None:
    # Test __lt__
    assert (prof1 < prof2) == (prof1.clearance_level < prof2.clearance_level)
    assert prof1.__lt__("invalid") is NotImplemented

    # Test __le__
    assert (prof1 <= prof2) == (prof1.clearance_level <= prof2.clearance_level)
    assert prof1.__le__("invalid") is NotImplemented

    # Test __gt__
    assert (prof1 > prof2) == (prof1.clearance_level > prof2.clearance_level)
    assert prof1.__gt__("invalid") is NotImplemented

    # Test __ge__
    assert (prof1 >= prof2) == (prof1.clearance_level >= prof2.clearance_level)
    assert prof1.__ge__("invalid") is NotImplemented


@given(st.sampled_from(list(RiskLevelPolicy)), st.sampled_from(list(RiskLevelPolicy)))
def test_risk_level_policy_comparisons(risk1: RiskLevelPolicy, risk2: RiskLevelPolicy) -> None:
    # Test __lt__
    assert (risk1 < risk2) == (risk1.weight < risk2.weight)
    assert risk1.__lt__("invalid") is NotImplemented

    # Test __le__
    assert (risk1 <= risk2) == (risk1.weight <= risk2.weight)
    assert risk1.__le__("invalid") is NotImplemented

    # Test __gt__
    assert (risk1 > risk2) == (risk1.weight > risk2.weight)
    assert risk1.__gt__("invalid") is NotImplemented

    # Test __ge__
    assert (risk1 >= risk2) == (risk1.weight >= risk2.weight)
    assert risk1.__ge__("invalid") is NotImplemented


@given(
    st.lists(st.sampled_from(list(SemanticClassificationProfile)), min_size=1, max_size=4),
    st.sampled_from(list(SemanticClassificationProfile)),
)
def test_workflow_manifest_lbac_dominance(
    allowed_classes: list[SemanticClassificationProfile], sla_max_class: SemanticClassificationProfile
) -> None:
    # Setup the required fields for WorkflowManifest
    prov = EpistemicProvenanceReceipt(
        extracted_by="did:node:id-1",
        source_event_cid="a" * 64,
        derivation_mode=DerivationModeProfile.DIRECT_TRANSLATION,
    )
    topology = DAGTopologyManifest(nodes={}, edges=[], max_depth=10, max_fan_out=10)
    sla = FederatedBilateralSLA(
        receiving_tenant_cid="tenant-x", max_permitted_classification=sla_max_class, liability_limit_magnitude=100
    )

    max_local_clearance = max(prof.clearance_level for prof in allowed_classes)

    if sla_max_class.clearance_level > max_local_clearance:
        with pytest.raises(ValidationError) as exc_info:
            WorkflowManifest(
                genesis_provenance=prov,
                manifest_version="1.0.0",
                topology=topology,
                allowed_semantic_classifications=allowed_classes,
                federated_sla=sla,
            )
        assert "LBAC Boundary Breach" in str(exc_info.value)
    else:
        manifest = WorkflowManifest(
            genesis_provenance=prov,
            manifest_version="1.0.0",
            topology=topology,
            allowed_semantic_classifications=allowed_classes,
            federated_sla=sla,
        )
        assert manifest.allowed_semantic_classifications is not None
        # Assert sorting works
        assert sorted(allowed_classes, key=lambda x: str(x.value)) == manifest.allowed_semantic_classifications


@given(st.lists(st.text(min_size=1, max_size=128), min_size=2, max_size=10, unique=True))
def test_smpc_topology_manifest_sorting(participant_cids: list[str]) -> None:
    # filter out non-matching DIDs
    dids = ["did:smpc:" + p for p in participant_cids]
    manifest = SMPCTopologyManifest(
        nodes={},
        smpc_protocol="garbled_circuits",
        joint_function_uri="https://example.com/circuit",
        participant_node_cids=dids,
    )
    assert manifest.participant_node_cids == sorted(dids)


@given(st.sampled_from([("did:node:gen1", "did:node:gen1"), ("did:node:eval1", "did:node:gen1")]))
def test_evaluator_optimizer_bipartite_nodes(nodes_pair: tuple[str, str]) -> None:
    gen_cid, eval_cid = nodes_pair
    # Populate the nodes dict with the gen_cid only
    from coreason_manifest.spec.ontology import AnyNodeProfile

    nodes: dict[str, AnyNodeProfile] = {gen_cid: CognitiveSystemNodeProfile(description="desc")}

    with pytest.raises(ValidationError) as exc_info:
        EvaluatorOptimizerTopologyManifest(
            nodes=nodes, generator_node_cid=gen_cid, evaluator_node_cid=eval_cid, max_revision_loops=5
        )

    # If they are the same, it fails the "cannot be the same node" or "not found"
    err_str = str(exc_info.value)
    assert "Generator and Evaluator cannot be the same node" in err_str or "not found in topology nodes" in err_str


@given(st.lists(st.tuples(st.text(min_size=1), st.floats(min_value=0.0, max_value=1.0)), min_size=1, max_size=5))
def test_evolutionary_topology_manifest_sorting(objectives_data: list[tuple[str, float]]) -> None:
    objectives = [
        FitnessObjectiveProfile(target_metric=name, weight=weight, direction="maximize")
        for name, weight in objectives_data
    ]
    mutation = MutationPolicy(mutation_rate=0.1, temperature_shift_variance=0.1)
    crossover = CrossoverPolicy(strategy_profile="single_point", blending_factor=0.5)

    manifest = EvolutionaryTopologyManifest(
        nodes={},
        generations=1,
        population_size=100,
        mutation=mutation,
        crossover=crossover,
        fitness_objectives=objectives,
    )
    # the @model_validator should sort objectives by target_metric
    assert manifest.fitness_objectives == sorted(objectives, key=lambda x: x.target_metric)
