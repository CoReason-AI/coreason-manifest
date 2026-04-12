import copy
import random

import pytest

from coreason_manifest.spec.ontology import (
    CognitiveActionSpaceManifest,
    PermissionBoundaryPolicy,
    RedactionPolicy,
    SaeLatentPolicy,
    SemanticClassificationProfile,
    SemanticFlowPolicy,
    SideEffectProfile,
    SpatialToolManifest,
    TransitionEdgeProfile,
)


def test_hash_invariance_semantic_flow_policy():
    """
    Generative test to prove that internal @model_validator hooks correctly stabilize
    the Merkle root by deterministically sorting lists.
    """

    # Construct synthetic data payload
    rules_payload = []
    for i in range(10):
        # We assign rule_cids out of order intentionally
        rule_cid = f"rule-{100 - i}"
        rule = RedactionPolicy(
            rule_cid=rule_cid,
            classification=SemanticClassificationProfile.CONFIDENTIAL,
            target_pattern="pattern.*",
            target_regex_pattern="^pattern.*$",
            context_exclusion_zones=[f"zone-{z}" for z in range(5)],
            action="redact",
            replacement_token="[REDACTED]",
        )
        rules_payload.append(rule)

    firewalls_payload = []
    for i in range(10):
        fw = SaeLatentPolicy(
            target_feature_index=100 - i,
            monitored_layers=[3, 1, 2],
            max_activation_threshold=0.5,
            violation_action="clamp",
            clamp_value=0.5,
            sae_dictionary_hash="a" * 64,
        )
        firewalls_payload.append(fw)

    # Base payload dictionary
    payload_a = {
        "policy_cid": "policy-123",
        "active": True,
        "rules": rules_payload,
        "latent_firewalls": firewalls_payload,
    }

    # Model A
    model_a = SemanticFlowPolicy(**payload_a)

    # Shuffle internal structures for Model B
    rules_shuffled = copy.deepcopy(rules_payload)
    random.shuffle(rules_shuffled)

    for rule in rules_shuffled:
        if rule.context_exclusion_zones:
            random.shuffle(rule.context_exclusion_zones)

    firewalls_shuffled = copy.deepcopy(firewalls_payload)
    random.shuffle(firewalls_shuffled)

    for fw in firewalls_shuffled:
        random.shuffle(fw.monitored_layers)

    payload_b = {
        "policy_cid": "policy-123",
        "active": True,
        "rules": rules_shuffled,
        "latent_firewalls": firewalls_shuffled,
    }

    # Model B
    model_b = SemanticFlowPolicy(**payload_b)

    # Mathematical Assertions
    assert hash(model_a) == hash(model_b), "Hash fracture detected! Insertion order modified the hash."
    assert model_a.model_dump_canonical() == model_b.model_dump_canonical(), (
        "Canonical serialization fracture detected!"
    )


if __name__ == "__main__":
    pytest.main([__file__])



def test_hash_invariance_cognitive_action_space():
    """
    Generative test to prove that internal @model_validator hooks correctly stabilize
    the Merkle root by deterministically sorting lists/dicts inside CognitiveActionSpaceManifest.
    """

    cap1 = SpatialToolManifest(
        tool_name="tool1",
        description="test tool",
        input_schema={},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    cap2 = SpatialToolManifest(
        tool_name="tool2",
        description="test tool 2",
        input_schema={},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    capabilities = {"cap1": cap1, "cap2": cap2}

    edges_payload = []
    for i in range(10):
        cap_id = f"cap{i}"
        capabilities[cap_id] = SpatialToolManifest(
            tool_name=f"tool{i}",
            description=f"test tool {i}",
            input_schema={},
            side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
            permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
        )
        edge = TransitionEdgeProfile(target_node_cid=cap_id, probability_weight=0.5, compute_weight_magnitude=100 - i)
        edges_payload.append(edge)

    payload_a = {
        "action_space_cid": "space-123",
        "capabilities": capabilities,
        "transition_matrix": {"cap1": edges_payload},
        "entry_point_cid": "cap1",
    }

    # Model A
    model_a = CognitiveActionSpaceManifest(**payload_a)

    # Shuffle internal structures for Model B
    edges_shuffled = copy.deepcopy(edges_payload)
    random.shuffle(edges_shuffled)

    payload_b = {
        "action_space_cid": "space-123",
        "capabilities": capabilities,
        "transition_matrix": {"cap1": edges_shuffled},
        "entry_point_cid": "cap1",
    }

    # Model B
    model_b = CognitiveActionSpaceManifest(**payload_b)

    # Mathematical Assertions
    assert hash(model_a) == hash(model_b), "Hash fracture detected! Insertion order modified the hash."
    assert model_a.model_dump_canonical() == model_b.model_dump_canonical(), (
        "Canonical serialization fracture detected!"
    )
