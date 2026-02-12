import pytest
from pathlib import Path
import json
import yaml
from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.utils.diff import ChangeCategory, compare_manifests
from coreason_manifest.utils.hashing import canonicalize, compute_integrity_hash, verify_chain
from coreason_manifest.utils.secure_io import SecureLoader, SecurityError
from coreason_manifest.spec.core.tools import ToolPack

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

    # 2. Integrity Hash (Aliases)
    class MockModel:
        # ARG002 Fix: Rename unused 'mode' to '_mode'
        def model_dump(self, mode, by_alias=False):
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

    # Add switch first to be entry point
    builder.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    builder.add_agent_ref("agent1", "profile1")

    # Connect
    builder.connect("switch1", "agent1")

    flow = builder.build()

    # 2. Diff
    builder2 = NewGraphFlow("test_flow", "1.1", "Test")
    builder2.define_profile("profile1", "assistant", "helpful")  # Same profile
    builder2.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    builder2.add_agent_ref("agent1", "profile1")
    builder2.connect("switch1", "agent1")

    # Add new node
    builder2.add_inspector("insp1", "target", "crit", "out")
    builder2.connect("agent1", "insp1")

    flow2 = builder2.build()

    changes = compare_manifests(flow, flow2)
    assert len(changes) > 0
    features = [c for c in changes if c.category == ChangeCategory.FEATURE]
    assert len(features) == 1
    assert features[0].path == "graph.nodes.insp1"

    # Test Resource Change
    builder3 = NewGraphFlow("test_flow", "1.2", "Test")
    builder3.add_computer_use("profile1", "assistant", "helpful", "gpt-4-computer")
    builder3.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    builder3.add_agent_ref("agent1", "profile1")
    builder3.connect("switch1", "agent1")
    flow3 = builder3.build()

    changes3 = compare_manifests(flow, flow3)
    resources = [c for c in changes3 if c.category == ChangeCategory.RESOURCE]
    assert len(resources) == 1
    assert resources[0].path == "definitions.profiles.profile1.reasoning.model"

    # Test Interface Diff
    builder4 = NewGraphFlow("test_flow", "1.3", "Test")
    builder4.set_interface(inputs={"new": "input"}, outputs={})
    # Copy graph - B007 Fix (Rename unused variable), PERF102 Fix (Use .values())
    for node in flow3.graph.nodes.values():
         builder4.add_node(node)
    builder4._edges = flow3.graph.edges
    # Copy definitions
    builder4._profiles = flow3.definitions.profiles

    flow4 = builder4.build()
    changes4 = compare_manifests(flow3, flow4)
    breaking = [c for c in changes4 if c.category == ChangeCategory.BREAKING]
    assert any(c.path == "interface" for c in breaking)

    # Test Tool Pack Diff
    builder5 = NewGraphFlow("test_flow", "1.4", "Test")
    # Same graph as flow3 - B007 Fix, PERF102 Fix
    for node in flow3.graph.nodes.values(): builder5.add_node(node)
    builder5._edges = flow3.graph.edges
    builder5._profiles = flow3.definitions.profiles

    # Valid ToolPack
    builder5.add_tool_pack(ToolPack(
        kind="ToolPack",
        namespace="newpack",
        tools=["t1"],
        dependencies=[],
        env_vars=[]
    ))
    flow5 = builder5.build()
    changes5 = compare_manifests(flow3, flow5)
    features = [c for c in changes5 if c.category == ChangeCategory.FEATURE]
    assert any(c.path == "definitions.tool_packs.newpack" for c in features)

def test_new_builder_methods() -> None:
    builder = NewGraphFlow("stream_b", "0.1", "Test")
    builder.define_profile("worker", "worker", "prompt")

    # Test Swarm
    builder.add_swarm("swarm1", "worker", "workload", concurrency=10)

    # Test Shadow Human
    builder.add_human_shadow("human1", "monitor me")

    builder.connect("swarm1", "human1")

    flow = builder.build()
    assert flow.graph.nodes["swarm1"].type == "swarm"
    assert flow.graph.nodes["swarm1"].max_concurrency == 10

    assert flow.graph.nodes["human1"].type == "human"
    assert flow.graph.nodes["human1"].interaction_mode == "shadow"
