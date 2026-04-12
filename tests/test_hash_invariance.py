import copy
import random

import pytest

from coreason_manifest.spec.ontology import (
    CognitiveActionSpaceManifest,
    CognitiveAgentNodeProfile,
    DraftingIntent,
    EpistemicSecurityProfile,
    ExecutionNodeReceipt,
    PermissionBoundaryPolicy,
    RedactionPolicy,
    SaeLatentPolicy,
    SemanticClassificationProfile,
    SemanticFlowPolicy,
    SideEffectProfile,
    SpatialHardwareProfile,
    SpatialToolManifest,
    TraceExportManifest,
    TransitionEdgeProfile,
)


def test_hash_invariance_semantic_flow_policy() -> None:
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
            replacement_token="[REDACTED]",  # noqa: S106
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
    # Model A
    model_a = SemanticFlowPolicy(
        policy_cid="policy-123",
        active=True,
        rules=rules_payload,
        latent_firewalls=firewalls_payload,
    )

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

    # Model B
    model_b = SemanticFlowPolicy(
        policy_cid="policy-123",
        active=True,
        rules=rules_shuffled,
        latent_firewalls=firewalls_shuffled,
    )

    # Mathematical Assertions
    assert hash(model_a) == hash(model_b), "Hash fracture detected! Insertion order modified the hash."
    assert model_a.model_dump_canonical() == model_b.model_dump_canonical(), (
        "Canonical serialization fracture detected!"
    )


if __name__ == "__main__":
    pytest.main([__file__])


def test_hash_invariance_cognitive_action_space() -> None:
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

    from typing import Any

    capabilities: dict[str, Any] = {"cap1": cap1, "cap2": cap2}

    edges_payload: list[Any] = []
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

    # Model A
    model_a = CognitiveActionSpaceManifest(
        action_space_cid="space-123",
        capabilities=capabilities,
        transition_matrix={"cap1": edges_payload},
        entry_point_cid="cap1",
    )

    # Shuffle internal structures for Model B
    edges_shuffled = copy.deepcopy(edges_payload)
    random.shuffle(edges_shuffled)

    # Model B
    model_b = CognitiveActionSpaceManifest(
        action_space_cid="space-123",
        capabilities=capabilities,
        transition_matrix={"cap1": edges_shuffled},
        entry_point_cid="cap1",
    )

    # Mathematical Assertions
    assert hash(model_a) == hash(model_b), "Hash fracture detected! Insertion order modified the hash."
    assert model_a.model_dump_canonical() == model_b.model_dump_canonical(), (
        "Canonical serialization fracture detected!"
    )


def test_trace_export_manifest_sort() -> None:
    node1 = ExecutionNodeReceipt(request_cid="req1", inputs={}, outputs={}, node_hash="a" * 64)
    node2 = ExecutionNodeReceipt(request_cid="req2", inputs={}, outputs={}, node_hash="b" * 64)
    # The order should be fixed by node_hash
    manifest = TraceExportManifest(batch_cid="batch-123", execution_nodes=[node2, node1])
    assert manifest.execution_nodes[0].node_hash == "a" * 64


def test_cognitive_agent_node_profile_sort() -> None:
    intent1 = DraftingIntent(context_prompt="prompt1", resolution_schema={}, timeout_action="rollback")

    intent2 = DraftingIntent(context_prompt="prompt2", resolution_schema={}, timeout_action="rollback")

    agent = CognitiveAgentNodeProfile(
        description="test agent",
        hardware=SpatialHardwareProfile(),
        security=EpistemicSecurityProfile(),
        emitted_intents=[intent2, intent1],
    )
    assert getattr(agent.emitted_intents[0], "context_prompt", "") == "prompt1"
