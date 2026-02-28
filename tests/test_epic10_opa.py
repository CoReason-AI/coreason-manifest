import json

from coreason_manifest.spec.core.oversight.governance import Governance


def test_governance_opa_policies() -> None:
    gov = Governance(opa_policies=["policy.rego", "inline_rules.rego"])
    assert gov.opa_policies == ["policy.rego", "inline_rules.rego"]  # noqa: S101

    dumped = gov.model_dump_json()
    parsed = json.loads(dumped)

    assert "opa_policies" in parsed  # noqa: S101
    assert parsed["opa_policies"] == ["policy.rego", "inline_rules.rego"]  # noqa: S101
