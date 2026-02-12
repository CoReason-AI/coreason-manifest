from coreason_manifest.utils.integrity import create_merkle_node, verify_merkle_proof


def test_integrity_chain_valid() -> None:
    # Genesis
    genesis = create_merkle_node(previous_hash="0", node_id="genesis", blackboard={"step": 0})
    chain = [genesis]

    # Step 1
    node1 = create_merkle_node(previous_hash=genesis.compute_hash(), node_id="node1", blackboard={"step": 1})
    chain.append(node1)

    # Step 2
    node2 = create_merkle_node(previous_hash=node1.compute_hash(), node_id="node2", blackboard={"step": 2})
    chain.append(node2)

    assert verify_merkle_proof(chain)


def test_integrity_chain_tampered() -> None:
    # Genesis
    genesis = create_merkle_node(previous_hash="0", node_id="genesis", blackboard={"step": 0})
    chain = [genesis]

    # Step 1
    node1 = create_merkle_node(previous_hash=genesis.compute_hash(), node_id="node1", blackboard={"step": 1})
    chain.append(node1)

    # Step 2
    node2 = create_merkle_node(previous_hash=node1.compute_hash(), node_id="node2", blackboard={"step": 2})
    chain.append(node2)

    # Tamper with node1 (e.g. modify blackboard hash, or node_id)
    # Since MerkleNode is frozen (pydantic), we can't modify in place easily.
    # We construct a fake node1 with same previous_hash but different content.
    fake_node1 = create_merkle_node(
        previous_hash=genesis.compute_hash(),
        node_id="node1",
        blackboard={"step": 999},  # Modified state
    )

    chain[1] = fake_node1
    # Now node2.previous_hash points to hash(original_node1).
    # hash(fake_node1) will be different.
    # So verification should fail at index 2 (node2).

    assert not verify_merkle_proof(chain)
