import json

from coreason_manifest.spec.ontology import (
    AnyStateEvent,
    ConformalPredictionBounds,
    DoublePushoutRewritingSchema,
    EpistemicDomainGraphManifest,
    EpistemicMappingContract,
    FederatedSourceProfile,
    GapPreservationConstraint,
    ParametricCoKleisliMorphism,
    TopologicalDataAnalysisProfile,
    TransmutationObservationEvent,
)


def test_epistemic_domain_graph_manifest_dpo_schemas_sort():
    dpo1 = DoublePushoutRewritingSchema(production_l={"a": "b"}, interface_k={}, replacement_r={})
    dpo2 = DoublePushoutRewritingSchema(production_l={"b": "a"}, interface_k={}, replacement_r={})

    manifest = EpistemicDomainGraphManifest(
        graph_id="g1",
        c_set_schema_hash="0" * 64,
        verified_axioms=[{"source_concept_id": "a", "directed_edge_type": "b", "target_concept_id": "c"}],
        dpo_schemas=[dpo1, dpo2],
    )

    expected = sorted(
        [dpo1, dpo2],
        key=lambda x: json.dumps(
            {
                "l": x.production_l,
                "k": x.interface_k,
                "r": x.replacement_r,
            },
            sort_keys=True,
        ),
    )

    assert manifest.dpo_schemas == expected


def test_parametric_cokleisli_morphism_sort():
    morph = ParametricCoKleisliMorphism(
        source_dialect_keys=["z", "a"],
        target_dids=["did:example:z", "did:example:a"],
        adjacency_matrix_comonad={"x": 1},
    )

    assert morph.source_dialect_keys == ["a", "z"]
    assert morph.target_dids == ["did:example:a", "did:example:z"]


def test_epistemic_mapping_contract():
    morph = ParametricCoKleisliMorphism(
        source_dialect_keys=["a"], target_dids=["did:example:a"], adjacency_matrix_comonad={}
    )
    contract = EpistemicMappingContract(contract_id="c1", mapping_rules=[morph])
    assert contract.mapping_rules == [morph]


def test_transmutation_observation_event_in_any_state_event():
    # just instantiate and test
    tda = TopologicalDataAnalysisProfile(
        betti_0_threshold=1, betti_1_persistence_limit=0.5, vietoris_rips_max_radius=0.5
    )
    cpb = ConformalPredictionBounds(empirical_miscoverage_rate_max=0.5, average_prediction_set_size_max=5)
    gpc = GapPreservationConstraint(min_representation_gap=0.5, distance_metric="cosine")
    fsp = FederatedSourceProfile(
        source_uri="http://example.com", node_cardinality=1, edge_cardinality=1, tda_profile=tda, conformal_bounds=cpb
    )

    event = TransmutationObservationEvent(event_id="e1", timestamp=0.0, source_profile=fsp, gap_constraint=gpc)

    # Can validate against AnyStateEvent logic by making a list
    import pydantic

    class Container(pydantic.BaseModel):
        evt: AnyStateEvent

    c = Container(evt=event)
    assert isinstance(c.evt, TransmutationObservationEvent)


def test_transmutation_observation_event_in_any_state_event_2():
    tda = TopologicalDataAnalysisProfile(
        betti_0_threshold=1, betti_1_persistence_limit=0.5, vietoris_rips_max_radius=0.5
    )
    cpb = ConformalPredictionBounds(empirical_miscoverage_rate_max=0.5, average_prediction_set_size_max=5)
    gpc = GapPreservationConstraint(min_representation_gap=0.5, distance_metric="cosine")
    fsp = FederatedSourceProfile(
        source_uri="http://example.com", node_cardinality=1, edge_cardinality=1, tda_profile=tda, conformal_bounds=cpb
    )

    event = TransmutationObservationEvent(event_id="e2", timestamp=0.0, source_profile=fsp, gap_constraint=gpc)

    from coreason_manifest.spec.ontology import EpistemicLedgerState

    ledger = EpistemicLedgerState(history=[event])
    assert len(ledger.history) == 1
    assert isinstance(ledger.history[0], TransmutationObservationEvent)
