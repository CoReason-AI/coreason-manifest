import random

from coreason_manifest.telemetry.custody import ExecutionNode, verify_merkle_proof


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

def test_sequence_type_hash_collision() -> None:
    """
    AGENT INSTRUCTION: Mathematically prove that lists, tuples, and sets
    containing identical elements map to distinct Merkle root hashes.
    """
    from coreason_manifest.telemetry.custody import ExecutionNode

    # Construct identical inner states represented in different sequence structures
    node_list = ExecutionNode(request_id="n1", inputs="a1", outputs={"data": [1, 2, 3]})
    node_tuple = ExecutionNode(request_id="n2", inputs="a1", outputs={"data": (1, 2, 3)})
    node_set = ExecutionNode(request_id="n3", inputs="a1", outputs={"data": {1, 2, 3}})

    hash_list = node_list.generate_node_hash()
    hash_tuple = node_tuple.generate_node_hash()
    hash_set = node_set.generate_node_hash()

    assert hash_list != hash_tuple, "CRITICAL: List and Tuple produced identical hashes"
    assert hash_list != hash_set, "CRITICAL: List and Set produced identical hashes"
    assert hash_tuple != hash_set, "CRITICAL: Tuple and Set produced identical hashes"
