# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import random

from coreason_manifest import ExecutionNode, verify_merkle_proof


def _generate_valid_chain(size: int) -> list[ExecutionNode]:
    """Generates a valid chain of ExecutionNode objects for testing."""
    chain: list[ExecutionNode] = []
    parent_hash: str | None = None

    for i in range(size):
        node = ExecutionNode(
            request_id=f"req_{i}",
            inputs={"input_data": f"data_{i}"},
            outputs={"output_data": f"data_{i}"},
            parent_hashes=[parent_hash] if parent_hash else [],
        )
        chain.append(node)
        parent_hash = node.node_hash

    return chain


def test_merkle_computational_integrity_failure() -> None:
    chain = _generate_valid_chain(3)

    # The Forgery
    tampered_node = chain[1].model_copy(update={"outputs": "hacked"})
    object.__setattr__(tampered_node, "node_hash", chain[1].node_hash)
    chain[1] = tampered_node

    # The SLA
    assert verify_merkle_proof(chain) is False


def test_merkle_topological_orphan_failure() -> None:
    chain = _generate_valid_chain(3)

    # The Forgery
    tampered_node = chain[2].model_copy(update={"parent_hashes": ["fake_sha256_hash"]})
    object.__setattr__(tampered_node, "node_hash", tampered_node.generate_node_hash())
    chain[2] = tampered_node

    # The SLA
    assert verify_merkle_proof(chain) is False


def test_merkle_asynchronous_jitter_resilience() -> None:
    chain = _generate_valid_chain(5)

    # The Perturbation
    random.shuffle(chain)

    # The SLA
    assert verify_merkle_proof(chain) is True
