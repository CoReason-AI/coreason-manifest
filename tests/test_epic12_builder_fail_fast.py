import pytest

from coreason_manifest.builder import NewLinearFlow
from coreason_manifest.spec.core.oversight.governance import Governance
from coreason_manifest.spec.core.primitives.types import RiskLevel


def test_builder_fail_fast_governance() -> None:
    builder = NewLinearFlow("fail_fast_flow", "1.0.0")

    # Set max_risk_level to STANDARD
    builder.set_governance(Governance(max_risk_level=RiskLevel.STANDARD))

    # Adding an agent with an unknown tool (defaults to CRITICAL) should fail fast
    with pytest.raises(
        ValueError, match=r"Tool 'unknown_tool_critical' exceeds the maximum allowed risk level for this flow\."
    ):
        builder.add_agent_ref("node1", "profile1", tools=["unknown_tool_critical"])
