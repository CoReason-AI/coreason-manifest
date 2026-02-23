import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import (
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.governance import Governance, ToolAccessPolicy
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack


def test_risk_governance_graph_flow() -> None:
    # Construct a flow with a critical tool
    critical_tool = ToolCapability(
        name="nuke_database", type="capability", risk_level="critical", description="Deletes all data."
    )

    pack = ToolPack(namespace="danger_ops", tools=[critical_tool])

    definitions = FlowDefinitions(tool_packs={"danger": pack})

    # Case 1: No kill switch
    flow = GraphFlow(
        metadata=FlowMetadata(name="DangerousFlow", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={}, edges=[]),
        definitions=definitions,
        governance=Governance(),  # No max_risk_level
    )
    assert flow.governance is not None
    assert flow.governance.max_risk_level is None

    # Case 2: Kill switch set to 'standard'
    with pytest.raises(ValidationError, match=r"Security Violation.*nuke_database.*critical.*exceeds.*standard"):
        GraphFlow(
            metadata=FlowMetadata(name="DangerousFlowBlocked", version="1.0.0"),
            interface=FlowInterface(),
            graph=Graph(nodes={}, edges=[]),
            definitions=definitions,
            governance=Governance(max_risk_level="standard"),
        )

    # Case 3: Kill switch set to 'critical' (should PASS)
    GraphFlow(
        metadata=FlowMetadata(name="DangerousFlowAllowed", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={}, edges=[]),
        definitions=definitions,
        governance=Governance(max_risk_level="critical"),
    )

    # Case 4: Tool with MISSING risk level with max_risk_level='standard' (should FAIL)
    raw_tool = {"name": "mystery_tool", "type": "capability"}  # Missing risk_level
    raw_pack = {"namespace": "mystery", "tools": [raw_tool]}

    with pytest.raises(ValidationError, match=r"Security Violation.*mystery_tool.*critical.*exceeds.*standard"):
        GraphFlow(
            metadata=FlowMetadata(name="MysteryFlow", version="1.0.0"),
            interface=FlowInterface(),
            graph=Graph(nodes={}, edges=[]),
            definitions=FlowDefinitions(tool_packs={"mystery": raw_pack}),
            governance=Governance(max_risk_level="standard"),
        )


def test_risk_governance_linear_flow() -> None:
    # Construct a flow with a critical tool
    critical_tool = ToolCapability(
        name="nuke_database", type="capability", risk_level="critical", description="Deletes all data."
    )

    pack = ToolPack(namespace="danger_ops", tools=[critical_tool])

    definitions = FlowDefinitions(tool_packs={"danger": pack})

    # Case 1: No kill switch
    LinearFlow(
        metadata=FlowMetadata(name="DangerousFlow", version="1.0.0"),
        steps=[],
        definitions=definitions,
        governance=Governance(),  # No max_risk_level
    )

    # Case 2: Kill switch set to 'standard'
    with pytest.raises(ValidationError, match=r"Security Violation.*nuke_database.*critical.*exceeds.*standard"):
        LinearFlow(
            metadata=FlowMetadata(name="DangerousFlowBlocked", version="1.0.0"),
            steps=[],
            definitions=definitions,
            governance=Governance(max_risk_level="standard"),
        )

    # Case 3: Kill switch set to 'critical' (should PASS)
    LinearFlow(
        metadata=FlowMetadata(name="DangerousFlowAllowed", version="1.0.0"),
        steps=[],
        definitions=definitions,
        governance=Governance(max_risk_level="critical"),
    )

    # Case 4: Tool with MISSING risk level with max_risk_level='standard' (should FAIL)
    raw_tool = {"name": "mystery_tool", "type": "capability"}  # Missing risk_level
    raw_pack = {"namespace": "mystery", "tools": [raw_tool]}

    with pytest.raises(ValidationError, match=r"Security Violation.*mystery_tool.*critical.*exceeds.*standard"):
        LinearFlow(
            metadata=FlowMetadata(name="MysteryFlow", version="1.0.0"),
            steps=[],
            definitions=FlowDefinitions(tool_packs={"mystery": raw_pack}),
            governance=Governance(max_risk_level="standard"),
        )


def test_risk_enum_update() -> None:
    # Test valid values
    ToolAccessPolicy(risk_level="safe")
    ToolAccessPolicy(risk_level="standard")
    ToolAccessPolicy(risk_level="critical", require_auth=True)

    # Test invalid value 'minimal'
    with pytest.raises(ValidationError):
        ToolAccessPolicy(risk_level="minimal")  # type: ignore


def test_validator_branches() -> None:
    # Coverage for "if not self.definitions or not self.definitions.tool_packs"
    # And "if not self.governance"

    # No governance
    GraphFlow(
        metadata=FlowMetadata(name="NoGov", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={}, edges=[]),
        definitions=None,
    )

    # Governance but no max_risk
    GraphFlow(
        metadata=FlowMetadata(name="GovNoMax", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={}, edges=[]),
        definitions=None,
        governance=Governance(),
    )

    # Governance with max_risk but no definitions
    GraphFlow(
        metadata=FlowMetadata(name="MaxRiskNoDefs", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={}, edges=[]),
        definitions=None,
        governance=Governance(max_risk_level="standard"),
    )

    # Governance with max_risk, definitions, but no tool packs
    GraphFlow(
        metadata=FlowMetadata(name="MaxRiskNoPacks", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={}, edges=[]),
        definitions=FlowDefinitions(),
        governance=Governance(max_risk_level="standard"),
    )

    # Coverage for LinearFlow similar branches
    LinearFlow(
        metadata=FlowMetadata(name="LMaxRiskNoPacks", version="1.0.0"),
        steps=[],
        definitions=FlowDefinitions(),
        governance=Governance(max_risk_level="standard"),
    )

    # LinearFlow: Tool defined as dict with explicit risk level (Hits line 300)
    l_explicit_risk_tool = {"name": "safe_tool", "type": "capability", "risk_level": "safe"}
    l_pack = {"namespace": "safe", "tools": [l_explicit_risk_tool]}

    LinearFlow(
        metadata=FlowMetadata(name="LExplicitRiskDict", version="1.0.0"),
        steps=[],
        definitions=FlowDefinitions(tool_packs={"safe": l_pack}),
        governance=Governance(max_risk_level="standard"),
    )

    # LinearFlow: Tool defined as dict with invalid risk level (Hits line 306)
    l_invalid_risk_tool = {"name": "invalid_risk_tool", "type": "capability", "risk_level": "unknown_risk"}
    l_pack_invalid = {"namespace": "invalid", "tools": [l_invalid_risk_tool]}

    with pytest.raises(ValidationError, match="Security Violation"):
        LinearFlow(
            metadata=FlowMetadata(name="LInvalidRiskDict", version="1.0.0"),
            steps=[],
            definitions=FlowDefinitions(tool_packs={"invalid": l_pack_invalid}),
            governance=Governance(max_risk_level="standard"),
        )

    # Coverage for tool defined as dict but with explicit risk level
    explicit_risk_tool = {"name": "safe_tool", "type": "capability", "risk_level": "safe"}
    pack = {"namespace": "safe", "tools": [explicit_risk_tool]}

    GraphFlow(
        metadata=FlowMetadata(name="ExplicitRiskDict", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={}, edges=[]),
        definitions=FlowDefinitions(tool_packs={"safe": pack}),
        governance=Governance(max_risk_level="standard"),
    )

    # Coverage for tool defined as dict but invalid risk level -> defaults to critical
    invalid_risk_tool = {"name": "invalid_risk_tool", "type": "capability", "risk_level": "unknown_risk"}
    pack_invalid = {"namespace": "invalid", "tools": [invalid_risk_tool]}

    with pytest.raises(ValidationError, match="Security Violation"):
        GraphFlow(
            metadata=FlowMetadata(name="InvalidRiskDict", version="1.0.0"),
            interface=FlowInterface(),
            graph=Graph(nodes={}, edges=[]),
            definitions=FlowDefinitions(tool_packs={"invalid": pack_invalid}),
            governance=Governance(max_risk_level="standard"),
        )
