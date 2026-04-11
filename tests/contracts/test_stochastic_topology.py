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
    HypothesisSuperposition,
    IdeationPhase,
    StochasticStateNode,
    StochasticTopology,
)


@given(
    st.lists(
        st.builds(
            StochasticStateNode,
            node_cid=st.uuids().map(str),
            parent_node_cid=st.none(),
            epistemic_entropy=st.floats(min_value=0.0, max_value=1.0),
        ),
        min_size=2,
        max_size=10,
    ),
    st.uuids().map(str),
)
def test_acyclic_dag_forward_reference(nodes: list[StochasticStateNode], topology_cid: str) -> None:
    nodes[0] = nodes[0].model_copy(update={"parent_node_cid": nodes[1].node_cid})
    with pytest.raises(ValidationError) as excinfo:
        StochasticTopology(topology_cid=topology_cid, phase=IdeationPhase.STOCHASTIC_DIFFUSION, stochastic_graph=nodes)
    assert "must appear before child node" in str(excinfo.value)


@given(st.builds(StochasticTopology, topology_cid=st.uuids().map(str), stochastic_graph=st.just([])))
def test_immutability_of_epistemic_status(topology: StochasticTopology) -> None:
    assert topology.epistemic_status == "stochastically_unbounded"
    with pytest.raises(ValidationError):
        topology.epistemic_status = "bounded"  # type: ignore[misc,assignment]


@given(
    st.builds(
        StochasticTopology,
        topology_cid=st.uuids().map(str),
        stochastic_graph=st.lists(
            st.builds(
                StochasticStateNode,
                node_cid=st.uuids().map(str),
                parent_node_cid=st.none(),
                epistemic_entropy=st.floats(min_value=0.0, max_value=1.0),
            ),
            max_size=5,
        ),
        superposition=st.one_of(
            st.none(),
            st.builds(
                HypothesisSuperposition,
                superposition_cid=st.uuids().map(str),
                competing_manifolds=st.just({}),
                wave_collapse_function=st.just("deterministic_compiler"),
            ),
        ),
    )
)
def test_serialization_isomorphism(topology: StochasticTopology) -> None:
    json_data = topology.model_dump_json()
    reconstructed = StochasticTopology.model_validate_json(json_data)
    assert topology == reconstructed
    assert topology.topology_cid == reconstructed.topology_cid
    assert len(topology.stochastic_graph) == len(reconstructed.stochastic_graph)
    for orig, recon in zip(topology.stochastic_graph, reconstructed.stochastic_graph, strict=True):
        assert orig.node_cid == recon.node_cid
