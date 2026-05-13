# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from coreason_manifest.spec.ontology import RiskLevelPolicy




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
