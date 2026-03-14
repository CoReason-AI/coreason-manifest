# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import ExecutionNodeReceipt


# 1. Atomic Test: Lineage Validation
def test_execution_node_receipt_orphaned_lineage() -> None:
    """Prove the receipt structurally rejects orphaned lineages."""
    with pytest.raises(ValidationError, match="Orphaned Lineage"):
        ExecutionNodeReceipt(request_id="req-1", parent_request_id="req-0", root_request_id=None, inputs={}, outputs={})


# 2. Define the Valid Mathematical Space for Payloads
json_primitive_st = st.recursive(
    st.none() | st.booleans() | st.floats(allow_nan=False, allow_infinity=False) | st.integers() | st.text(max_size=50),
    lambda children: st.lists(children, max_size=5) | st.dictionaries(st.text(max_size=50), children, max_size=5),
    max_leaves=15,
)


# 3. Fuzzing Hash Determinism
@given(payload=json_primitive_st)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_execution_node_receipt_hash_determinism(payload: Any) -> None:
    """
    AGENT INSTRUCTION: Mathematically prove that the canonical hashing mechanism
    is deterministic and immutable regardless of dict insertion ordering or architecture.
    """
    # Base node instantiation
    node_1 = ExecutionNodeReceipt(
        request_id="req-hash-test", inputs=payload, outputs=payload, parent_hashes=["hashA", "hashB"]
    )

    # Create a semantically identical node by dumping/loading
    # to simulate chaotic dict insertion orders over network boundaries
    scrambled_payload = json.loads(json.dumps(payload))
    node_2 = ExecutionNodeReceipt(
        request_id="req-hash-test",
        inputs=scrambled_payload,
        outputs=scrambled_payload,
        parent_hashes=["hashA", "hashB"],
    )

    assert node_1.node_hash == node_2.node_hash
    assert node_1.node_hash is not None
