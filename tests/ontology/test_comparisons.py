from coreason_manifest.spec.ontology import RiskLevelPolicy, SemanticClassificationProfile


def test_semantic_classification_profile_exists() -> None:
    # Verify the profile members exist
    assert SemanticClassificationProfile.PUBLIC.value == "public"
    assert SemanticClassificationProfile.INTERNAL.value == "internal"
    assert SemanticClassificationProfile.CONFIDENTIAL.value == "confidential"
    assert SemanticClassificationProfile.RESTRICTED.value == "restricted"


def test_risk_level_policy_comparisons() -> None:
    s = RiskLevelPolicy.SAFE
    st = RiskLevelPolicy.STANDARD
    c = RiskLevelPolicy.CRITICAL

    assert s < st
    assert st <= c
    assert c > st
    assert c >= s
    assert s.weight == 0
    assert st.weight == 1
    assert c.weight == 2

    assert s.__lt__(123) is NotImplemented
    assert s.__le__(123) is NotImplemented
    assert c.__gt__(123) is NotImplemented
    assert c.__ge__(123) is NotImplemented
