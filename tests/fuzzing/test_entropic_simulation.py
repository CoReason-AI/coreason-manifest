import math

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import HypothesisSuperposition, StochasticStateNode


@given(st.text(max_size=100000), st.uuids().map(str))
def test_maximum_entropy_injection(chaotic_text: str, node_cid: str) -> None:
    # Ensure Pydantic successfully parses the chaotic unicode payload
    node = StochasticStateNode(
        node_cid=node_cid, agent_role="generator", stochastic_tensor=chaotic_text, epistemic_entropy=0.5
    )
    assert node.stochastic_tensor == chaotic_text


@given(st.floats(), st.uuids().map(str), st.uuids().map(str))
def test_float_boundary_warfare(chaotic_float: float, node_cid: str, super_cid: str) -> None:
    # If the float is within bounds [0.0, 1.0] and not NaN, it should succeed
    if 0.0 <= chaotic_float <= 1.0 and not math.isnan(chaotic_float):
        StochasticStateNode(
            node_cid=node_cid, agent_role="critic", stochastic_tensor="test", epistemic_entropy=chaotic_float
        )
        HypothesisSuperposition(
            superposition_cid=super_cid,
            wave_collapse_function="highest_confidence",
            competing_manifolds={"test": chaotic_float},
            residual_entropy_vectors=[],
        )
    else:
        # Otherwise it should raise ValidationError, proving deterministic bounds
        with pytest.raises(ValidationError):
            StochasticStateNode(
                node_cid=node_cid, agent_role="critic", stochastic_tensor="test", epistemic_entropy=chaotic_float
            )

        with pytest.raises(ValidationError):
            HypothesisSuperposition(
                superposition_cid=super_cid,
                wave_collapse_function="highest_confidence",
                competing_manifolds={"test": chaotic_float},
                residual_entropy_vectors=[],
            )
