from coreason_manifest.spec.ontology import RiskLevelPolicy, SemanticClassificationProfile


def test_semantic_classification_comparisons():
    p = SemanticClassificationProfile.PUBLIC
    i = SemanticClassificationProfile.INTERNAL
    c = SemanticClassificationProfile.CONFIDENTIAL
    r = SemanticClassificationProfile.RESTRICTED

    assert p < i
    assert i <= c
    assert r > c
    assert r >= p
    assert p.clearance_level == 0
    assert r.clearance_level == 3

    assert p.__lt__(123) is NotImplemented
    assert p.__le__(123) is NotImplemented
    assert r.__gt__(123) is NotImplemented
    assert r.__ge__(123) is NotImplemented


def test_risk_level_policy_comparisons():
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
