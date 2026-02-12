import pytest
from pathlib import Path
import json
import yaml
from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.utils.diff import ChangeCategory, compare_manifests
from coreason_manifest.utils.hashing import canonicalize, compute_integrity_hash, verify_chain
from coreason_manifest.utils.secure_io import SecureLoader, SecurityError
from coreason_manifest.spec.core.tools import ToolPack
from typing import Any

@pytest.fixture
def jail_dir(tmp_path: Path) -> Path:
    jail = tmp_path / "jail"
    jail.mkdir()
    return jail

def test_secure_loader(jail_dir: Path) -> None:
    loader = SecureLoader(jail_dir, max_depth=5)

    # 1. Test Jail Enforcement
    with open(jail_dir / "safe.yaml", "w") as f:
        f.write("key: value")

    # Try to access file outside jail
    outside = jail_dir.parent / "outside.yaml"
    with open(outside, "w") as f:
        f.write("secret: true")

    # Testing absolute path outside jail
    with pytest.raises(SecurityError):
        loader.load(outside)

    # Try to ref outside
    with open(jail_dir / "bad_ref.yaml", "w") as f:
        f.write('ref: {"$ref": "../outside.yaml"}')

    with pytest.raises(SecurityError):
        loader.load(jail_dir / "bad_ref.yaml")

    # Test Absolute Path Bypass Attempt (New)
    abs_outside = str(outside.resolve())
    with open(jail_dir / "bypass.yaml", "w") as f:
        f.write(f'ref: {{"$ref": "{abs_outside}"}}')

    with pytest.raises(SecurityError, match="Absolute paths are forbidden"):
        loader.load(jail_dir / "bypass.yaml")

    # 2. Test Recursive Resolution
    with open(jail_dir / "main.yaml", "w") as f:
        f.write('sub: {"$ref": "sub.yaml"}')
    with open(jail_dir / "sub.yaml", "w") as f:
        f.write("value: 123")

    data = loader.load(jail_dir / "main.yaml")
    assert data["sub"]["value"] == 123

    # 3. Test Cycle Detection
    with open(jail_dir / "cycle_a.yaml", "w") as f:
        f.write('b: {"$ref": "cycle_b.yaml"}')
    with open(jail_dir / "cycle_b.yaml", "w") as f:
        f.write('a: {"$ref": "cycle_a.yaml"}')

    with pytest.raises(RecursionError, match="Circular dependency"):
        loader.load(jail_dir / "cycle_a.yaml")

    # 4. Test Max Depth (New)
    for i in range(7):
        with open(jail_dir / f"depth_{i}.yaml", "w") as f:
             f.write(f'next: {{"$ref": "depth_{i+1}.yaml"}}')
    with open(jail_dir / "depth_7.yaml", "w") as f:
        f.write("val: end")

    with pytest.raises(RecursionError, match="Max recursion depth"):
        loader.load(jail_dir / "depth_0.yaml")

def test_hashing() -> None:
    # 1. Canonicalization
    data1 = {"b": 2, "a": 1}
    data2 = {"a": 1, "b": 2}
    assert canonicalize(data1) == canonicalize(data2)

    # Float handling
    assert canonicalize({"val": 20.0}) == b'{"val":20}'
    assert canonicalize({"val": 20.5}) == b'{"val":20.5}'

    # NaN/Inf check
    with pytest.raises(ValueError, match="NaN/Infinity not allowed"):
        canonicalize({"val": float('inf')})

    # 2. Integrity Hash (Aliases)
    class MockModel:
        # Revert to 'mode' to support keyword argument calls from hashing.py
        def model_dump(self, mode: str | None = None, by_alias: bool = False) -> dict[str, Any]: # noqa: ARG002
            if by_alias:
                return {"previousHash": "abc"}
            return {"previous_hash": "abc"}

    entry = MockModel()
    h = compute_integrity_hash(entry)
    expected = compute_integrity_hash({"previousHash": "abc"})
    assert h == expected

    # 3. Chain Verification
    entry1 = {"id": 1, "data": "genesis", "previous_hash": None}
    h1 = compute_integrity_hash(entry1)
    entry1["integrity_hash"] = h1

    entry2 = {"id": 2, "data": "next", "previousHash": h1}
    h2 = compute_integrity_hash(entry2)
    entry2["integrityHash"] = h2

    chain = [entry1, entry2]
    assert verify_chain(chain)

def test_builder_and_diff() -> None:
    # 1. Build Graph
    builder = NewGraphFlow("test_flow", "1.0", "Test")

    # Add profile for agent
    builder.define_profile("profile1", "assistant", "helpful")

    # Add tool pack so agent tools are valid
    builder.add_tool_pack(ToolPack(kind="ToolPack", namespace="base", tools=["search", "calculator"], dependencies=[], env_vars=[]))

    # Add switch first to be entry point
    builder.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    builder.add_agent_ref("agent1", "profile1", tools=["search"])

    # Connect
    builder.connect("switch1", "agent1")

    flow = builder.build()

    # 2. Diff
    builder2 = NewGraphFlow("test_flow", "1.1", "Test")
    builder2.define_profile("profile1", "assistant", "helpful")  # Same profile
    builder2.add_tool_pack(ToolPack(kind="ToolPack", namespace="base", tools=["search", "calculator"], dependencies=[], env_vars=[]))

    builder2.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    builder2.add_agent_ref("agent1", "profile1", tools=["calculator"]) # Changed tool
    builder2.connect("switch1", "agent1")

    # Add new node and connect it to avoid orphan warning
    builder2.add_inspector("insp1", "target", "crit", "out")
    builder2.connect("agent1", "insp1")

    flow2 = builder2.build()

    changes = compare_manifests(flow, flow2)

    # Check tool changes
    breaking = [c for c in changes if c.category == ChangeCategory.BREAKING and c.path == "graph.nodes.agent1.tools"]
    assert len(breaking) == 1
    assert breaking[0].old == ["search"]

    features = [c for c in changes if c.category == ChangeCategory.FEATURE and c.path == "graph.nodes.agent1.tools"]
    assert len(features) == 1
    assert features[0].new == ["calculator"]

    # 3. Diff (Inspector Criteria)
    builder3 = NewGraphFlow("test_flow", "1.2", "Test")
    # ... setup flow3 with inspector change ...
    builder_insp = NewGraphFlow("insp_flow", "1.0", "Test")
    builder_insp.add_inspector("insp1", "target", "loose", "out")
    flow_insp = builder_insp.build()

    builder_insp2 = NewGraphFlow("insp_flow", "1.1", "Test")
    builder_insp2.add_inspector("insp1", "target", "strict", "out")
    flow_insp2 = builder_insp2.build()

    changes_insp = compare_manifests(flow_insp, flow_insp2)
    governance = [c for c in changes_insp if c.category == ChangeCategory.GOVERNANCE]
    assert len(governance) == 1
    assert governance[0].path == "graph.nodes.insp1.criteria"

    # Test Resource Change (Model)
    # Reusing builders properly
    builder_res = NewGraphFlow("res_flow", "1.0", "Test")
    builder_res.define_profile("profile1", "assistant", "helpful")
    builder_res.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    builder_res.add_agent_ref("agent1", "profile1")
    builder_res.connect("switch1", "agent1")
    flow_res = builder_res.build()

    builder_res2 = NewGraphFlow("res_flow", "1.1", "Test")
    # Model change via computer use shortcut
    builder_res2.add_computer_use("profile1", "assistant", "helpful", "gpt-4-computer")
    builder_res2.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    builder_res2.add_agent_ref("agent1", "profile1")
    builder_res2.connect("switch1", "agent1")
    flow_res2 = builder_res2.build()

    changes_res = compare_manifests(flow_res, flow_res2)
    resources = [c for c in changes_res if c.category == ChangeCategory.RESOURCE]
    assert len(resources) == 1
    assert resources[0].path == "definitions.profiles.profile1.reasoning.model"

    # Test Interface Diff
    builder_int = NewGraphFlow("test_flow", "1.3", "Test")
    builder_int.set_interface(inputs={"new": "input"}, outputs={})
    # Copy graph from valid flow
    for node in flow.graph.nodes.values():
         builder_int.add_node(node)
    builder_int._edges = flow.graph.edges
    # Copy definitions
    assert flow.definitions is not None
    builder_int._profiles = flow.definitions.profiles
    builder_int._tool_packs = flow.definitions.tool_packs

    flow_int = builder_int.build()
    changes_int = compare_manifests(flow, flow_int)
    breaking = [c for c in changes_int if c.category == ChangeCategory.BREAKING]
    assert any(c.path == "interface" for c in breaking)

    # Test Tool Pack Diff
    builder_tp = NewGraphFlow("test_flow", "1.4", "Test")
    for node in flow.graph.nodes.values(): builder_tp.add_node(node)
    builder_tp._edges = flow.graph.edges
    builder_tp._profiles = flow.definitions.profiles
    builder_tp._tool_packs = flow.definitions.tool_packs.copy()

    # Valid ToolPack
    builder_tp.add_tool_pack(ToolPack(
        kind="ToolPack",
        namespace="newpack",
        tools=["t1"],
        dependencies=[],
        env_vars=[]
    ))
    flow_tp = builder_tp.build()
    changes_tp = compare_manifests(flow, flow_tp)
    features = [c for c in changes_tp if c.category == ChangeCategory.FEATURE]
    assert any(c.path == "definitions.tool_packs.newpack" for c in features)

def test_new_builder_methods() -> None:
    builder = NewGraphFlow("stream_b", "0.1", "Test")
    builder.define_profile("worker", "worker", "prompt")

    # Test Swarm
    builder.add_swarm("swarm1", "worker", "workload", concurrency=10, aggregator_model="gpt-4")

    # Test Shadow Human
    builder.add_human_shadow("human1", "monitor me")

    builder.connect("swarm1", "human1")

    flow = builder.build()
    assert flow.graph.nodes["swarm1"].type == "swarm"
    assert flow.graph.nodes["swarm1"].max_concurrency == 10
    # Check aggregator model (can be string or ModelCriteria, here passed as string)
    assert flow.graph.nodes["swarm1"].aggregator_model == "gpt-4"

    assert flow.graph.nodes["human1"].type == "human"
    assert flow.graph.nodes["human1"].interaction_mode == "shadow"

def test_diff_logic() -> None:
    # 1. Agent Tool Reordering
    builder = NewGraphFlow("test", "1.0", "Test")
    builder.define_profile("p1", "role", "persona")
    # Need to register tools
    builder.add_tool_pack(ToolPack(kind="ToolPack", namespace="base", tools=["t1", "t2"], dependencies=[], env_vars=[]))

    builder.add_agent_ref("a1", "p1", tools=["t1", "t2"])
    flow1 = builder.build()

    builder2 = NewGraphFlow("test", "1.1", "Test")
    builder2.define_profile("p1", "role", "persona")
    builder2.add_tool_pack(ToolPack(kind="ToolPack", namespace="base", tools=["t1", "t2"], dependencies=[], env_vars=[]))
    builder2.add_agent_ref("a1", "p1", tools=["t2", "t1"]) # Reordered
    flow2 = builder2.build()

    changes = compare_manifests(flow1, flow2)
    # Expect PATCH for reorder
    patches = [c for c in changes if c.category == ChangeCategory.PATCH and c.path == "graph.nodes.a1.tools"]
    assert len(patches) == 1

    # 2. Switch Logic
    builder3 = NewGraphFlow("test", "1.0", "Test")
    builder3.define_profile("p1", "role", "persona")
    # Make 's1' the first node to avoid orphan warning if it's entry
    builder3.add_switch("s1", "var", {"case1": "c1"}, "default")
    builder3.add_agent_ref("default", "p1")
    builder3.add_agent_ref("c1", "p1")
    builder3.connect("s1", "c1")
    builder3.connect("s1", "default")
    flow3 = builder3.build()

    builder4 = NewGraphFlow("test", "1.1", "Test")
    builder4.define_profile("p1", "role", "persona")
    # Make 's1' first
    builder4.add_switch("s1", "var", {}, "default")
    builder4.add_agent_ref("default", "p1")
    builder4.add_agent_ref("c1", "p1")
    # Remove case1
    builder4.connect("s1", "default")
    # c1 is orphaned but since s1 is entry, validation might pass warnings?
    # To be safe, connect default to c1? No, logic change is what we test.
    # We can connect default -> c1 to ensure connectivity.
    builder4.connect("default", "c1")

    flow4 = builder4.build()

    changes2 = compare_manifests(flow3, flow4)
    # Expect BREAKING for removed case
    breaking = [c for c in changes2 if c.category == ChangeCategory.BREAKING and c.path == "graph.nodes.s1.cases"]
    assert len(breaking) == 1
    assert breaking[0].old == ["case1"]
