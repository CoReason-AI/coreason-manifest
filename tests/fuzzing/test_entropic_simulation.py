# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import math
import uuid

from hypothesis import given, strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.stochastic import StochasticConsensus, StochasticStateNode


@given(st.text(max_size=100000))
def test_maximum_entropy_injection(chaotic_text: str):
    """
    Assertion 1: Inject maximum entropy chaotic Unicode into stochastic_tensor
    and prove topological structures handle unbounded semantic weight.
    """
    node = StochasticStateNode(
        node_cid=uuid.uuid4(),
        agent_role="generator",
        stochastic_tensor=chaotic_text,
        epistemic_entropy=0.5,
    )

    # Assert string mapping holds
    assert node.stochastic_tensor == chaotic_text

    # Assert JSON dumps/loads correctly parses the max entropy text payload
    json_payload = node.model_dump_json()
    restored_node = StochasticStateNode.model_validate_json(json_payload)

    assert restored_node.stochastic_tensor == chaotic_text


@given(st.floats())
def test_float_boundary_warfare(chaotic_float: float):
    """
    Assertion 2: Inject unbounded floats (NaN, Infinity, negatives, numbers > 1)
    into epistemic_entropy and convergence_confidence, asserting rejection without crashing.
    """
    # If the randomly generated float is mathematically valid (0.0 <= x <= 1.0)
    # and not NaN, it should succeed. Otherwise, it should raise ValidationError.

    is_valid = not math.isnan(chaotic_float) and (0.0 <= chaotic_float <= 1.0)

    # Test StochasticStateNode bounds
    if not is_valid:
        try:
            StochasticStateNode(
                node_cid=uuid.uuid4(),
                agent_role="critic",
                stochastic_tensor="test",
                epistemic_entropy=chaotic_float,
            )
            assert False, f"Should have raised ValidationError for epistemic_entropy: {chaotic_float}"
        except ValidationError:
            pass
    else:
        node = StochasticStateNode(
            node_cid=uuid.uuid4(),
            agent_role="critic",
            stochastic_tensor="test",
            epistemic_entropy=chaotic_float,
        )
        assert node.epistemic_entropy == chaotic_float

    # Test StochasticConsensus bounds
    if not is_valid:
        try:
            StochasticConsensus(
                consensus_cid=uuid.uuid4(),
                proposed_manifold="manifold",
                convergence_confidence=chaotic_float,
                residual_entropy_vectors=[],
            )
            assert False, f"Should have raised ValidationError for convergence_confidence: {chaotic_float}"
        except ValidationError:
            pass
    else:
        consensus = StochasticConsensus(
            consensus_cid=uuid.uuid4(),
            proposed_manifold="manifold",
            convergence_confidence=chaotic_float,
            residual_entropy_vectors=[],
        )
        assert consensus.convergence_confidence == chaotic_float
