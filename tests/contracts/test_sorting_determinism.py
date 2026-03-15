import hashlib

from coreason_manifest.spec.ontology import ActionSpaceManifest, ConceptBottleneckPolicy


def test_concept_bottleneck_dictionary_sorting() -> None:
    policy = ConceptBottleneckPolicy(
        bottleneck_temperature=0.0,
        explanation_modality="contrastive",
        required_concept_vector={"zeta_concept": True, "alpha_concept": False, "omega_concept": True},
    )
    assert list(policy.required_concept_vector.keys()) == ["alpha_concept", "omega_concept", "zeta_concept"]


def test_action_space_array_sorting() -> None:
    manifest = ActionSpaceManifest.model_validate(
        {
            "action_space_id": "test-action-space",
            "allowed_discovery_namespaces": ["ext:zebra", "ext:alpha", "ext:bravo"],
        },
        context={"allowed_ext_intents": {"ext:zebra", "ext:alpha", "ext:bravo"}},
    )
    assert manifest.allowed_discovery_namespaces == ["ext:alpha", "ext:bravo", "ext:zebra"]


def test_rfc8785_canonical_hashing_consistency() -> None:
    manifest_a = ActionSpaceManifest.model_validate(
        {"action_space_id": "test-action-space", "allowed_discovery_namespaces": ["ext:foo", "ext:bar", "ext:baz"]},
        context={"allowed_ext_intents": {"ext:foo", "ext:bar", "ext:baz"}},
    )
    manifest_b = ActionSpaceManifest.model_validate(
        {"action_space_id": "test-action-space", "allowed_discovery_namespaces": ["ext:baz", "ext:foo", "ext:bar"]},
        context={"allowed_ext_intents": {"ext:foo", "ext:bar", "ext:baz"}},
    )

    hash_a = hashlib.sha256(manifest_a.model_dump_canonical()).hexdigest()
    hash_b = hashlib.sha256(manifest_b.model_dump_canonical()).hexdigest()

    assert hash_a == hash_b
