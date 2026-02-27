import pytest
from coreason_manifest.spec.core.contracts import ActionNode, AtomicSkill, StrictPayload
from coreason_manifest.spec.core.flow import FlowSpec, Graph, FlowMetadata, FlowInterface
from coreason_manifest.utils.gatekeeper import _enforce_red_button_rule, _is_guarded
from coreason_manifest.spec.core.constants import NodeCapability

def test_gatekeeper_entry_point_bypass_fix():
    # Node with computer_use (needs guard) is the entry point
    skill = AtomicSkill(capabilities=[NodeCapability.COMPUTER_USE])
    node = ActionNode(id="risky_entry", type="action", skill=skill)

    graph = Graph(nodes={"risky_entry": node}, edges=[], entry_point="risky_entry")
    flow = FlowSpec(metadata=FlowMetadata(name="test", version="1.0.0"), graph=graph, interface=FlowInterface())

    # Run enforcement
    reports = _enforce_red_button_rule([node], flow, {})

    assert len(reports) == 1
    patch = reports[0].remediation.patch_data

    # Check if entry point is replaced
    entry_point_patch = next((op for op in patch if op["path"] == "/graph/entry_point"), None)
    assert entry_point_patch is not None
    assert entry_point_patch["op"] == "replace"
    assert entry_point_patch["value"].startswith("guard_risky_entry")

def test_gatekeeper_id_collision():
    skill = AtomicSkill(capabilities=[NodeCapability.COMPUTER_USE])
    node = ActionNode(id="n1", type="action", skill=skill)

    # Existing guard node
    existing_guard = ActionNode(id="guard_n1", type="action", skill=AtomicSkill(capabilities=["human_approval"]))

    graph = Graph(nodes={"n1": node, "guard_n1": existing_guard}, edges=[], entry_point="n1")
    flow = FlowSpec(metadata=FlowMetadata(name="test", version="1.0.0"), graph=graph, interface=FlowInterface())

    reports = _enforce_red_button_rule([node], flow, {})

    patch = reports[0].remediation.patch_data
    # Check that new guard ID is not "guard_n1"
    add_node_op = next((op for op in patch if op["op"] == "add" and op["path"].startswith("/graph/nodes/")), None)
    new_guard_id = add_node_op["path"].split("/")[-1]

    assert new_guard_id != "guard_n1"
    assert new_guard_id.startswith("guard_n1_")
