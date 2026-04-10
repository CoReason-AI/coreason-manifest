import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    IdeationPhase,
    StochasticConsensus,
    StochasticStateNode,
    StochasticTopology,
)


@given(
    st.lists(
        st.builds(
            StochasticStateNode, parent_node_cid=st.none(), epistemic_entropy=st.floats(min_value=0.0, max_value=1.0)
        ),
        min_size=2,
        max_size=10,
    )
)
def test_acyclic_dag_forward_reference(nodes):
    # Setup a cycle: The first node points to the second node
    nodes[0] = nodes[0].model_copy(update={"parent_node_cid": nodes[1].node_cid})

    with pytest.raises(ValidationError) as excinfo:
        StochasticTopology(phase=IdeationPhase.STOCHASTIC_DIFFUSION, stochastic_graph=nodes)
    assert "must appear before child node" in str(excinfo.value)


@given(st.builds(StochasticTopology, stochastic_graph=st.just([])))
def test_immutability_of_epistemic_status(topology):
    assert topology.epistemic_status == "stochastically_unbounded"

    with pytest.raises(ValidationError):
        # Attempting to assign to a model with validate_assignment=True
        topology.epistemic_status = "bounded"


@given(
    st.builds(
        StochasticTopology,
        stochastic_graph=st.lists(
            st.builds(
                StochasticStateNode,
                parent_node_cid=st.none(),
                epistemic_entropy=st.floats(min_value=0.0, max_value=1.0),
            ),
            max_size=5,
        ),
        consensus=st.one_of(
            st.none(), st.builds(StochasticConsensus, convergence_confidence=st.floats(min_value=0.0, max_value=1.0))
        ),
    )
)
def test_serialization_isomorphism(topology):
    # Check serialization
    json_data = topology.model_dump_json()
    reconstructed = StochasticTopology.model_validate_json(json_data)

    # Assert zero-loss by ensuring they are completely equal
    assert topology == reconstructed

    # Prove the _cid lineages remain intact
    assert topology.topology_cid == reconstructed.topology_cid
    assert len(topology.stochastic_graph) == len(reconstructed.stochastic_graph)
    for orig, recon in zip(topology.stochastic_graph, reconstructed.stochastic_graph, strict=True):
        assert orig.node_cid == recon.node_cid
