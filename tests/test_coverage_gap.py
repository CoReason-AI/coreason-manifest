import pytest
import os
import json
from typing import Any, cast
from unittest.mock import MagicMock, patch
from pathlib import Path

from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.utils.diff import compare_manifests, ChangeCategory, _diff_switch_node, _diff_agent_node, DiffChange
from coreason_manifest.utils.hashing import canonicalize, compute_integrity_hash, verify_chain
from coreason_manifest.utils.secure_io import SecureLoader, SecurityError
from coreason_manifest.spec.core.flow import GraphFlow, Graph, FlowInterface, FlowMetadata, FlowDefinitions
from coreason_manifest.spec.core.nodes import SwitchNode, InspectorNode, AgentNode, CognitiveProfile
from coreason_manifest.spec.core.tools import ToolPack
from coreason_manifest.spec.core.engines import StandardReasoning, Supervision, ComputerUseReasoning
from coreason_manifest.spec.core.governance import Governance
from pydantic import BaseModel

# --- Builder Tests ---

def test_builder_add_computer_use() -> None:
    builder = NewGraphFlow("ComputerUse", "1.0", "Desc")
    builder.add_computer_use(
        profile_id="comp_use_profile",
        role="operator",
        persona="expert",
        model="gpt-4-vision",
        actions=["click", "type"]
    )
    # Verify profile was added
    assert "comp_use_profile" in builder._profiles
    profile = builder._profiles["comp_use_profile"]

    # Type assertion for mypy
    assert isinstance(profile.reasoning, ComputerUseReasoning)
    assert profile.reasoning.type == "computer_use"
    assert profile.reasoning.model == "gpt-4-vision"
    assert profile.reasoning.allowed_actions == ["click", "type"]

    # Test default actions
    builder.add_computer_use(
        profile_id="comp_use_default",
        role="operator",
        persona="expert",
        model="gpt-4-vision",
    )
    profile_def = builder._profiles["comp_use_default"]

    assert isinstance(profile_def.reasoning, ComputerUseReasoning)
    # We need to check if default actions were applied.
    assert "scroll" in profile_def.reasoning.allowed_actions
    assert "screenshot" in profile_def.reasoning.allowed_actions

def test_builder_validate_flow_errors() -> None:
    # Mock validate_flow to return errors
    with patch("coreason_manifest.builder.validate_flow", return_value=["Error 1", "Error 2"]):
        builder = NewGraphFlow("Invalid", "1.0", "Desc")
        # Need a profile for the agent node to pass Pydantic validation inside build()
        builder.define_profile("p1", "role", "persona")
        # Add a dummy node so build() proceeds past likely empty checks if any
        builder.add_node(AgentNode(id="n1", type="agent", profile="p1", tools=[], metadata={}, supervision=None))

        with pytest.raises(ValueError, match="Validation failed:\n- Error 1\n- Error 2"):
            builder.build()

def test_builder_add_switch() -> None:
    builder = NewGraphFlow("Switch", "1.0", "Desc")
    builder.add_switch("s1", "var", {"a": "t1"}, "default")
    assert "s1" in builder._nodes
    node = builder._nodes["s1"]
    assert node.type == "switch"
    # assert isinstance(node, SwitchNode) # implied by type check, but helps mypy if needed
    # SwitchNode has variable
    if isinstance(node, SwitchNode):
        assert node.variable == "var"

def test_builder_add_emergence_inspector() -> None:
    builder = NewGraphFlow("Emergence", "1.0", "Desc")
    builder.add_emergence_inspector(
        node_id="e1",
        target="var",
        criteria="crit",
        output="out",
        judge_model="gpt-4"
    )
    assert "e1" in builder._nodes
    node = builder._nodes["e1"]
    assert node.type == "emergence_inspector"
    # assert isinstance(node, EmergenceInspectorNode) # Not imported, but we can check attribute dynamically or import it
    assert getattr(node, "judge_model", "") == "gpt-4"

def test_builder_connect_missing_source() -> None:
    builder = NewGraphFlow("Connect", "1.0", "Desc")
    builder.add_node(SwitchNode(id="t1", type="switch", variable="v", cases={}, default="d", metadata={}, supervision=None))
    # Source "s1" missing
    builder.connect("s1", "t1")

    with pytest.raises(ValueError, match="Edge source 's1' not found"):
        builder.build()

def test_builder_connect_missing_target() -> None:
    builder = NewGraphFlow("Connect", "1.0", "Desc")
    builder.add_node(SwitchNode(id="s1", type="switch", variable="v", cases={}, default="d", metadata={}, supervision=None))
    # Target "t1" missing
    builder.connect("s1", "t1")

    with pytest.raises(ValueError, match="Edge target 't1' not found"):
        builder.build()

# --- Diff Tests ---

def test_diff_tool_packs() -> None:
    tp1 = ToolPack(kind="ToolPack", namespace="p1", tools=[], dependencies=[], env_vars=[])
    tp2 = ToolPack(kind="ToolPack", namespace="p2", tools=[], dependencies=[], env_vars=[])

    # definitions
    def_old = FlowDefinitions(profiles={}, tool_packs={"p1": tp1})
    def_new = FlowDefinitions(profiles={}, tool_packs={"p1": tp1, "p2": tp2})

    old = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="Old", version="1", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={}, edges=[]), definitions=def_old)
    new = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="New", version="2", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={}, edges=[]), definitions=def_new)

    changes: list[DiffChange] = compare_manifests(old, new)
    # Added p2 -> FEATURE
    assert any(c.path == "definitions.tool_packs.p2" and c.category == ChangeCategory.FEATURE for c in changes)

    # Removed
    def_old_2 = FlowDefinitions(profiles={}, tool_packs={"p1": tp1, "p2": tp2})
    def_new_2 = FlowDefinitions(profiles={}, tool_packs={"p1": tp1})

    old_2 = old.model_copy(update={"definitions": def_old_2})
    new_2 = new.model_copy(update={"definitions": def_new_2})

    changes = compare_manifests(old_2, new_2)
    # Removed p2 -> BREAKING
    assert any(c.path == "definitions.tool_packs.p2" and c.category == ChangeCategory.BREAKING for c in changes)

    # Changed
    tp1_v2 = ToolPack(kind="ToolPack", namespace="p1", tools=["t1"], dependencies=[], env_vars=[])

    def_old_3 = FlowDefinitions(profiles={}, tool_packs={"p1": tp1})
    def_new_3 = FlowDefinitions(profiles={}, tool_packs={"p1": tp1_v2})

    old_3 = old.model_copy(update={"definitions": def_old_3})
    new_3 = new.model_copy(update={"definitions": def_new_3})

    changes = compare_manifests(old_3, new_3)
    # Changed p1 -> BREAKING (item_category for tool_packs)
    assert any(c.path == "definitions.tool_packs.p1" and c.category == ChangeCategory.BREAKING for c in changes)


def test_diff_profiles() -> None:
    # Mock profiles
    p1_old = CognitiveProfile(role="r", persona="p", reasoning=StandardReasoning(model="gpt-3.5"), fast_path=None)
    p1_new = CognitiveProfile(role="r", persona="p", reasoning=StandardReasoning(model="gpt-4"), fast_path=None)

    def_old = FlowDefinitions(profiles={"p1": p1_old}, tool_packs={})
    def_new = FlowDefinitions(profiles={"p1": p1_new}, tool_packs={})

    old = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="Old", version="1", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={}, edges=[]), definitions=def_old)
    new = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="New", version="2", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={}, edges=[]), definitions=def_new)

    # Resource change (model)
    changes: list[DiffChange] = compare_manifests(old, new)
    assert any(c.path == "definitions.profiles.p1.reasoning.model" and c.category == ChangeCategory.RESOURCE for c in changes)

    # Patch change (other field)
    p1_new_2 = CognitiveProfile(role="new_role", persona="p", reasoning=StandardReasoning(model="gpt-3.5"), fast_path=None)
    def_new_2 = FlowDefinitions(profiles={"p1": p1_new_2}, tool_packs={})

    new_2 = new.model_copy(update={"definitions": def_new_2})

    # Need to revert old to have gpt-3.5 (already has it)

    changes = compare_manifests(old, new_2)
    assert any(c.path == "definitions.profiles.p1" and c.category == ChangeCategory.PATCH for c in changes)

def test_diff_switch_node() -> None:
    old_node = SwitchNode(id="s1", type="switch", variable="v", cases={"a": "n1"}, default="n2", metadata={}, supervision=None)
    new_node = SwitchNode(id="s1", type="switch", variable="v", cases={"a": "n1", "b": "n3"}, default="n2", metadata={}, supervision=None)

    changes: list[DiffChange] = []
    # Add case
    _diff_switch_node("nodes.s1", old_node, new_node, changes)
    assert any(c.path == "nodes.s1.cases" and c.category == ChangeCategory.FEATURE for c in changes)

    # Remove case
    changes = []
    _diff_switch_node("nodes.s1", new_node, old_node, changes)
    assert any(c.path == "nodes.s1.cases" and c.category == ChangeCategory.BREAKING for c in changes)

    # Change target
    new_node_changed = SwitchNode(id="s1", type="switch", variable="v", cases={"a": "n3"}, default="n2", metadata={}, supervision=None)
    changes = []
    _diff_switch_node("nodes.s1", old_node, new_node_changed, changes)
    assert any(c.path == "nodes.s1.cases.a" and c.category == ChangeCategory.PATCH for c in changes)

def test_diff_agent_node_tools() -> None:
    old = AgentNode(id="a1", type="agent", profile="p1", tools=["t1", "t2"], metadata={}, supervision=None)
    new = AgentNode(id="a1", type="agent", profile="p1", tools=["t2", "t1"], metadata={}, supervision=None)

    changes: list[DiffChange] = []
    _diff_agent_node("nodes.a1", old, new, changes)
    # Order changed -> PATCH
    assert any(c.path == "nodes.a1.tools" and c.category == ChangeCategory.PATCH for c in changes)

    # Profile ref change
    new_profile = AgentNode(id="a1", type="agent", profile="p2", tools=["t1", "t2"], metadata={}, supervision=None)
    changes = []
    _diff_agent_node("nodes.a1", old, new_profile, changes)
    assert any(c.path == "nodes.a1.profile" and c.category == ChangeCategory.PATCH for c in changes)

def test_diff_governance() -> None:
    gov_old = Governance(rate_limit_rpm=10)
    gov_new = Governance(rate_limit_rpm=20)

    old = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="Old", version="1", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={}, edges=[]), definitions=FlowDefinitions(profiles={}, tool_packs={}), governance=gov_old)
    new = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="New", version="2", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={}, edges=[]), definitions=FlowDefinitions(profiles={}, tool_packs={}), governance=gov_new)

    changes: list[DiffChange] = compare_manifests(old, new)
    assert any(c.path == "governance" and c.category == ChangeCategory.GOVERNANCE for c in changes)

def test_diff_node_type_change() -> None:
    old = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="Old", version="1", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={"n1": SwitchNode(id="n1", type="switch", variable="v", cases={}, default="d", metadata={}, supervision=None)}, edges=[]), definitions=FlowDefinitions(profiles={}, tool_packs={}))

    # New node has same ID but different type (e.g. InspectorNode)
    new_node = InspectorNode(id="n1", type="inspector", target_variable="t", criteria="c", output_variable="o", metadata={}, supervision=None)

    new = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="New", version="2", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={"n1": new_node}, edges=[]), definitions=FlowDefinitions(profiles={}, tool_packs={}))

    changes: list[DiffChange] = compare_manifests(old, new)
    assert any(c.path == "graph.nodes.n1.type" and c.category == ChangeCategory.BREAKING for c in changes)

def test_diff_node_supervision_change() -> None:
    s1 = Supervision(max_retries=1, strategy="escalate", backoff_factor=1.0, retry_delay_seconds=1.0, fallback=None)
    s2 = Supervision(max_retries=2, strategy="escalate", backoff_factor=1.0, retry_delay_seconds=1.0, fallback=None)

    node1 = SwitchNode(id="n1", type="switch", variable="v", cases={}, default="d", metadata={}, supervision=s1)
    node2 = SwitchNode(id="n1", type="switch", variable="v", cases={}, default="d", metadata={}, supervision=s2)

    old = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="Old", version="1", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={"n1": node1}, edges=[]), definitions=FlowDefinitions(profiles={}, tool_packs={}))
    new = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="New", version="2", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={"n1": node2}, edges=[]), definitions=FlowDefinitions(profiles={}, tool_packs={}))

    changes: list[DiffChange] = compare_manifests(old, new)
    assert any(c.path == "graph.nodes.n1.supervision" and c.category == ChangeCategory.RESOURCE for c in changes)

def test_diff_node_metadata_change() -> None:
    node1 = SwitchNode(id="n1", type="switch", variable="v", cases={}, default="d", metadata={"k": "v1"}, supervision=None)
    node2 = SwitchNode(id="n1", type="switch", variable="v", cases={}, default="d", metadata={"k": "v2"}, supervision=None)

    old = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="Old", version="1", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={"n1": node1}, edges=[]), definitions=FlowDefinitions(profiles={}, tool_packs={}))
    new = GraphFlow(kind="GraphFlow", metadata=FlowMetadata(name="New", version="2", description="", tags=[]), interface=FlowInterface(inputs={}, outputs={}), blackboard=None, graph=Graph(nodes={"n1": node2}, edges=[]), definitions=FlowDefinitions(profiles={}, tool_packs={}))

    changes: list[DiffChange] = compare_manifests(old, new)
    assert any(c.path == "graph.nodes.n1" and c.category == ChangeCategory.PATCH for c in changes)

# --- Hashing Tests ---

def test_hashing_floats() -> None:
    assert canonicalize(20.0) == b"20"

    with pytest.raises(ValueError, match="NaN/Infinity not allowed"):
        canonicalize(float("nan"))

    with pytest.raises(ValueError, match="NaN/Infinity not allowed"):
        canonicalize(float("inf"))

    with pytest.raises(ValueError, match="NaN/Infinity not allowed"):
        canonicalize(float("-inf"))

def test_hashing_recursive() -> None:
    data = {"a": {"b": [1.0, 2]}}
    assert canonicalize(data) == b'{"a":{"b":[1,2]}}'

def test_verify_chain_missing_hash() -> None:
    # Entry without stored hash
    chain = [{"data": "foo"}]
    assert not verify_chain(chain)

def test_verify_chain_bad_hash() -> None:
    entry = {"data": "foo", "integrity_hash": "bad"}
    assert not verify_chain([entry])

def test_verify_chain_broken_link() -> None:
    entry1 = {"data": "foo"}
    entry1["integrity_hash"] = compute_integrity_hash(entry1)

    entry2 = {"data": "bar", "previous_hash": "bad_link"}
    entry2["integrity_hash"] = compute_integrity_hash(entry2)

    chain = [entry1, entry2]
    assert not verify_chain(chain)

def test_verify_chain_object_access() -> None:
    class Entry:
        def __init__(self, data: str, prev: str | None = None) -> None:
            self.data = data
            self.previous_hash = prev
            self.integrity_hash: str | None = None

        def model_dump(self, **kwargs: Any) -> dict[str, Any]:
            d = {"data": self.data}
            if self.previous_hash:
                d["previous_hash"] = self.previous_hash
            if self.integrity_hash:
                d["integrity_hash"] = self.integrity_hash
            return d

    e1 = Entry("foo")
    e1.integrity_hash = compute_integrity_hash(e1)

    e2 = Entry("bar", e1.integrity_hash)
    e2.integrity_hash = compute_integrity_hash(e2)

    # Valid chain of objects
    assert verify_chain([e1, e2])

    # Invalid object hash
    e1.integrity_hash = "wrong"
    assert not verify_chain([e1])


class MyModel(BaseModel):
    data: str
    integrity_hash: str | None = None

def test_hashing_pydantic() -> None:
    m = MyModel(data="foo")
    h = compute_integrity_hash(m)
    assert h

    # Test verify_chain with pydantic models
    m.integrity_hash = h
    assert verify_chain([m])

def test_canonicalize_pydantic() -> None:
    m = MyModel(data="foo")
    # This calls _prepare_for_jcs with a Pydantic model, hitting line 25
    assert b"foo" in canonicalize(m)

def test_hashing_primitive() -> None:
    # Test primitive type to hit 'else' in compute_integrity_hash
    h = compute_integrity_hash("simple_string")
    assert h

def test_hashing_exclude_fields() -> None:
    entry = {"a": 1, "b": 2}
    # Hash without exclusion
    h1 = compute_integrity_hash(entry)
    # Hash with exclusion of 'b'
    h2 = compute_integrity_hash(entry, exclude_fields={"b"})

    assert h1 != h2

    entry_only_a = {"a": 1}
    h_only_a = compute_integrity_hash(entry_only_a)
    assert h2 == h_only_a


# --- Secure IO Tests ---

def test_secure_loader_jail_escape_initial(tmp_path: Path) -> None:
    root = tmp_path / "jail"
    root.mkdir()
    loader = SecureLoader(root)

    outside = tmp_path / "outside.yaml"
    outside.write_text("foo: bar")

    with pytest.raises(SecurityError, match="Initial file .* is outside the jail"):
        loader.load(outside)

def test_secure_loader_different_drive(tmp_path: Path) -> None:
    root = tmp_path / "jail"
    root.mkdir()
    loader = SecureLoader(root)
    inside = root / "inside.yaml"
    inside.write_text("foo: bar")

    # Mock os.path.commonpath to raise ValueError (simulating different drives)
    with patch("os.path.commonpath", side_effect=ValueError):
        with pytest.raises(SecurityError, match="Initial file .* is outside the jail"):
            loader.load(inside)

def test_secure_loader_resolve_ref_different_drive(tmp_path: Path) -> None:
    root = tmp_path / "jail"
    root.mkdir()
    loader = SecureLoader(root)

    # inside.yaml refers to something
    inside = root / "inside.yaml"
    inside.write_text("$ref: ref.yaml")

    # We need to mock inside resolve_ref.
    # Since load() calls resolve_ref, we can test it via load() if we mock carefully.
    # But resolve_ref is called after reading file.

    # Let's test resolve_ref directly
    with patch("os.path.commonpath", side_effect=ValueError):
        with pytest.raises(SecurityError, match="Access denied: Path .* is on a different drive"):
             loader.resolve_ref(inside, "ref.yaml")

def test_secure_loader_type_error(tmp_path: Path) -> None:
    root = tmp_path / "jail"
    root.mkdir()
    loader = SecureLoader(root)

    # File with list
    bad = root / "list.yaml"
    bad.write_text("- item1\n- item2")

    with pytest.raises(TypeError, match="Expected dict at root"):
        loader.load(bad)

def test_secure_loader_recursion(tmp_path: Path) -> None:
    root = tmp_path / "jail"
    root.mkdir()

    # a -> b -> a
    (root / "a.yaml").write_text("$ref: b.yaml")
    (root / "b.yaml").write_text("$ref: a.yaml")

    loader = SecureLoader(root)
    with pytest.raises(RecursionError, match="Circular dependency detected"):
        loader.load(root / "a.yaml")

    # Depth limit
    # a -> b (max depth 0)
    (root / "depth.yaml").write_text("$ref: other.yaml")
    (root / "other.yaml").write_text("foo: bar")

    loader_shallow = SecureLoader(root, max_depth=0)
    with pytest.raises(RecursionError, match="Max recursion depth"):
        loader_shallow.load(root / "depth.yaml")

def test_secure_loader_file_not_found(tmp_path: Path) -> None:
    root = tmp_path / "jail"
    root.mkdir()
    loader = SecureLoader(root)

    # Refer to non-existent file
    inside = root / "inside.yaml"
    inside.write_text("$ref: non_existent.yaml")

    with pytest.raises(FileNotFoundError, match="File not found"):
        loader.load(inside)

def test_secure_loader_scalar_content(tmp_path: Path) -> None:
    root = tmp_path / "jail"
    root.mkdir()
    loader = SecureLoader(root)

    scalar = root / "scalar.yaml"
    scalar.write_text("just a string")

    # Should return the string, as line 78 returns result
    result = loader.load(scalar)

    # Casting to match expected string result, since load returns dict[str, Any]
    # In practice, if YAML loads as scalar, the type ignore/cast is appropriate in test
    assert cast(str, result) == "just a string"

def test_secure_loader_invalid_ref_type(tmp_path: Path) -> None:
    root = tmp_path / "jail"
    root.mkdir()
    loader = SecureLoader(root)

    bad_ref = root / "bad_ref.yaml"
    bad_ref.write_text("$ref: 123")

    with pytest.raises(ValueError, match="Invalid \\$ref value"):
        loader.load(bad_ref)
