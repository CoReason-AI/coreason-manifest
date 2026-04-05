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

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    AnyStateEvent,
    ConformalPredictionBounds,
    DoublePushoutRewritingSchema,
    EpistemicAxiomState,
    EpistemicDomainGraphManifest,
    EpistemicMappingContract,
    EpistemicTransmutationIntent,
    FederatedSourceProfile,
    GapPreservationConstraint,
    MorphologicalExpansionBounds,
    ParametricCoKleisliMorphism,
    ProfunctorOpticContract,
    ProfunctorOpticType,
    TopologicalDataAnalysisProfile,
    TopologicalFunctorContract,
    TransformationCardinalityProfile,
    TransmutationDriftEvent,
    TransmutationObservationEvent,
)


@given(
    l_keys=st.lists(st.text(min_size=1, max_size=255), min_size=1, max_size=5),
    l_vals=st.lists(st.integers(), min_size=1, max_size=5),
    k_keys=st.lists(st.text(min_size=1, max_size=255), min_size=1, max_size=5),
    k_vals=st.lists(st.integers(), min_size=1, max_size=5),
)
def test_epistemic_domain_graph_manifest_dpo_schemas_sort(
    l_keys: list[str], l_vals: list[int], k_keys: list[str], k_vals: list[int]
) -> None:
    l_dict: dict[str, Any] = dict(zip(l_keys, l_vals, strict=False))
    k_dict: dict[str, Any] = dict(zip(k_keys, k_vals, strict=False))

    dpo1 = DoublePushoutRewritingSchema(production_l=l_dict, interface_k=k_dict, replacement_r={})
    dpo2 = DoublePushoutRewritingSchema(production_l=k_dict, interface_k=l_dict, replacement_r={})

    manifest = EpistemicDomainGraphManifest(
        graph_id="g1",
        c_set_schema_hash="0" * 64,
        verified_axioms=[EpistemicAxiomState(source_concept_id="a", directed_edge_type="b", target_concept_id="c")],
        dpo_schemas=[dpo1, dpo2],
    )

    expected = sorted([dpo1, dpo2], key=lambda x: x.model_dump_canonical())

    assert manifest.dpo_schemas == expected


@given(
    target_dids=st.lists(st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True), min_size=1, max_size=10),
)
def test_parametric_cokleisli_morphism_sort(target_dids: list[str]) -> None:
    optic = ProfunctorOpticContract(
        optic_type=ProfunctorOpticType.LENS, source_focus_pointer="/a", target_injection_pointer="/b"
    )
    morph = ParametricCoKleisliMorphism(
        optic_mappings=[optic],
        target_dids=target_dids,
        adjacency_matrix_comonad={},
    )

    assert morph.optic_mappings == [optic]
    assert morph.target_dids == sorted(target_dids)


@given(
    target_dids=st.lists(st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True), min_size=1, max_size=5),
)
def test_epistemic_mapping_contract(target_dids: list[str]) -> None:
    optic = ProfunctorOpticContract(
        optic_type=ProfunctorOpticType.LENS, source_focus_pointer="/a", target_injection_pointer="/b"
    )
    morph = ParametricCoKleisliMorphism(optic_mappings=[optic], target_dids=target_dids, adjacency_matrix_comonad={})
    contract = EpistemicMappingContract(contract_id="c1", mapping_rules=[morph])
    assert contract.mapping_rules == [morph]


@given(
    betti0=st.integers(min_value=1, max_value=100),
    betti1=st.floats(min_value=0.0, max_value=1.0),
    radius=st.floats(min_value=0.0, max_value=100.0),
    emr=st.floats(min_value=0.0, max_value=1.0),
    apss=st.integers(min_value=1, max_value=100),
    gap=st.floats(min_value=0.0, max_value=1.0),
    metric=st.sampled_from(["cosine", "euclidean", "earth_movers"]),
)
def test_transmutation_observation_event_in_any_state_event(
    betti0: int, betti1: float, radius: float, emr: float, apss: int, gap: float, metric: str
) -> None:
    # just instantiate and test
    tda = TopologicalDataAnalysisProfile(
        betti_0_threshold=betti0, betti_1_persistence_limit=betti1, vietoris_rips_max_radius=radius
    )
    cpb = ConformalPredictionBounds(empirical_miscoverage_rate_max=emr, average_prediction_set_size_max=apss)

    # Have to bypass mypy dynamically here for Literal metric
    gpc = GapPreservationConstraint(min_representation_gap=gap, distance_metric=metric)  # type: ignore
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


@given(
    betti0=st.integers(min_value=1, max_value=100),
    betti1=st.floats(min_value=0.0, max_value=1.0),
    radius=st.floats(min_value=0.0, max_value=100.0),
    emr=st.floats(min_value=0.0, max_value=1.0),
    apss=st.integers(min_value=1, max_value=100),
    gap=st.floats(min_value=0.0, max_value=1.0),
    metric=st.sampled_from(["cosine", "euclidean", "earth_movers"]),
)
def test_transmutation_observation_event_in_any_state_event_2(
    betti0: int, betti1: float, radius: float, emr: float, apss: int, gap: float, metric: str
) -> None:
    tda = TopologicalDataAnalysisProfile(
        betti_0_threshold=betti0, betti_1_persistence_limit=betti1, vietoris_rips_max_radius=radius
    )
    cpb = ConformalPredictionBounds(empirical_miscoverage_rate_max=emr, average_prediction_set_size_max=apss)
    gpc = GapPreservationConstraint(min_representation_gap=gap, distance_metric=metric)  # type: ignore
    fsp = FederatedSourceProfile(
        source_uri="http://example.com", node_cardinality=1, edge_cardinality=1, tda_profile=tda, conformal_bounds=cpb
    )

    event = TransmutationObservationEvent(event_id="e2", timestamp=0.0, source_profile=fsp, gap_constraint=gpc)

    from coreason_manifest.spec.ontology import EpistemicLedgerState

    ledger = EpistemicLedgerState(history=[event])
    assert len(ledger.history) == 1
    assert isinstance(ledger.history[0], TransmutationObservationEvent)


@given(
    contract_id=st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True),
    source_hash=st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True),
    target_hash=st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True),
    cardinality_rule=st.sampled_from(list(TransformationCardinalityProfile)),
)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_topological_functor_contract(
    contract_id: str, source_hash: str, target_hash: str, cardinality_rule: TransformationCardinalityProfile
) -> None:
    if cardinality_rule == TransformationCardinalityProfile.LEFT_KAN_EXTENSION:
        expansion_bounds = MorphologicalExpansionBounds(max_fan_out=10, entropy_preservation_threshold=0.5)
    else:
        expansion_bounds = None

    contract = TopologicalFunctorContract(
        contract_id=contract_id,
        source_schema_hash=source_hash,
        target_schema_hash=target_hash,
        cardinality_rule=cardinality_rule,
        expansion_bounds=expansion_bounds,
    )
    assert contract.contract_id == contract_id
    assert contract.cardinality_rule == cardinality_rule


@given(
    functor_contract_id=st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True),
    source_coords=st.lists(st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True), min_size=1, max_size=10),
    target_cids=st.lists(st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True), min_size=1, max_size=10),
    payload_key=st.text(min_size=1, max_size=255),
    payload_val=st.text(max_size=100),
)
def test_epistemic_transmutation_intent(
    functor_contract_id: str, source_coords: list[str], target_cids: list[str], payload_key: str, payload_val: str
) -> None:
    intent = EpistemicTransmutationIntent(
        functor_contract_id=functor_contract_id,
        source_coordinates=source_coords,
        target_cids=target_cids,
        domain_payload={payload_key: payload_val},
    )
    assert intent.source_coordinates == sorted(source_coords)
    assert intent.target_cids == sorted(target_cids)


@given(
    event_id=st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True),
    timestamp=st.floats(min_value=0.0, max_value=1e9),
    source_card=st.integers(min_value=0, max_value=1000),
    target_card=st.integers(min_value=0, max_value=1000),
    target_functor_id=st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True),
)
def test_transmutation_drift_event(
    event_id: str, timestamp: float, source_card: int, target_card: int, target_functor_id: str
) -> None:
    event = TransmutationDriftEvent(
        event_id=event_id,
        timestamp=timestamp,
        source_vector_cardinality=source_card,
        actual_target_cardinality=target_card,
        target_functor_id=target_functor_id,
    )
    assert event.source_vector_cardinality == source_card
    assert event.actual_target_cardinality == target_card
