import pytest
from pydantic import ValidationError
from hypothesis import given, strategies as st
from coreason_manifest.spec.ontology import (
    StochasticStateNode,
    StochasticConsensus
)
import math

@given(st.text(max_size=100000))
def test_maximum_entropy_injection(chaotic_text):
    # Ensure Pydantic successfully parses the chaotic unicode payload
    node = StochasticStateNode(
        agent_role="generator",
        stochastic_tensor=chaotic_text,
        epistemic_entropy=0.5
    )
    assert node.stochastic_tensor == chaotic_text

@given(st.floats())
def test_float_boundary_warfare(chaotic_float):
    # If the float is within bounds [0.0, 1.0] and not NaN, it should succeed
    if 0.0 <= chaotic_float <= 1.0 and not math.isnan(chaotic_float):
        StochasticStateNode(
            agent_role="critic",
            stochastic_tensor="test",
            epistemic_entropy=chaotic_float
        )
        StochasticConsensus(
            proposed_manifold="test",
            convergence_confidence=chaotic_float,
            residual_entropy_vectors=[]
        )
    else:
        # Otherwise it should raise ValidationError, proving deterministic bounds
        with pytest.raises(ValidationError):
            StochasticStateNode(
                agent_role="critic",
                stochastic_tensor="test",
                epistemic_entropy=chaotic_float
            )

        with pytest.raises(ValidationError):
            StochasticConsensus(
                proposed_manifold="test",
                convergence_confidence=chaotic_float,
                residual_entropy_vectors=[]
            )
