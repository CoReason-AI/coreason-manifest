import json

from coreason_manifest.spec.core.oversight.governance import Governance
from coreason_manifest.utils.validator import _validate_governance


def test_governance_opa_policies() -> None:
    gov = Governance(opa_policies=["policy.rego", "inline_rules.rego"])
    assert gov.opa_policies == ["policy.rego", "inline_rules.rego"]  # noqa: S101

    dumped = gov.model_dump_json()
    parsed = json.loads(dumped)

    assert "opa_policies" in parsed  # noqa: S101
    assert parsed["opa_policies"] == ["policy.rego", "inline_rules.rego"]  # noqa: S101


def test_opa_policies_validation() -> None:
    # Test that OPA policies without a hard risk ceiling yield an error
    gov = Governance(opa_policies=["policy.rego"])

    errors = _validate_governance(gov, set())

    assert len(errors) == 1  # noqa: S101
    assert errors[0].code == "ERR_GOV_INVALID_CONFIG"  # noqa: S101
    assert errors[0].severity == "violation"  # noqa: S101
    assert (  # noqa: S101
        errors[0].message
        == "Declarative OPA policies must be mathematically backed by a hard risk ceiling in a zero-trust architecture."
    )

    # Test that OPA policies with a hard risk ceiling do not yield an error
    from coreason_manifest.spec.core.primitives.types import RiskLevel

    gov_valid = Governance(opa_policies=["policy.rego"], max_risk_level=RiskLevel.STANDARD)
    errors_valid = _validate_governance(gov_valid, set())
    assert len(errors_valid) == 0  # noqa: S101
