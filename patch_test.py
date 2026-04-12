with open("tests/test_hash_invariance.py") as f:
    content = f.read()

target = """    edges_payload = []
    for i in range(10):
        # We assign targets out of order
        target_cid = "cap2" if i % 2 == 0 else "cap1"
        edge = TransitionEdgeProfile(
            target_node_cid=target_cid,
            probability_weight=0.5,
            compute_weight_magnitude=100 - i
        )
        edges_payload.append(edge)"""

replacement = """    edges_payload = []
    for i in range(10):
        cap_id = f"cap{i}"
        capabilities[cap_id] = SpatialToolManifest(
            tool_name=f"tool{i}",
            description=f"test tool {i}",
            input_schema={},
            side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
            permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True)
        )
        edge = TransitionEdgeProfile(
            target_node_cid=cap_id,
            probability_weight=0.5,
            compute_weight_magnitude=100 - i
        )
        edges_payload.append(edge)"""

content = content.replace(target, replacement)

with open("tests/test_hash_invariance.py", "w") as f:
    f.write(content)
