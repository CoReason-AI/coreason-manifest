import pytest
from pathlib import Path
import json
import yaml
from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.utils.diff import ChangeCategory, compare_manifests
from coreason_manifest.utils.hashing import canonicalize, compute_integrity_hash, verify_chain
from coreason_manifest.utils.secure_io import SecureLoader, SecurityError

@pytest.fixture
def jail_dir(tmp_path: Path) -> Path:
    jail = tmp_path / "jail"
    jail.mkdir()
    return jail

def test_secure_loader(jail_dir: Path) -> None:
    loader = SecureLoader(jail_dir)

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

    with pytest.raises(RecursionError):
        loader.load(jail_dir / "cycle_a.yaml")

    # 4. Diamond Dependency (Should be allowed)
    # A -> B, A -> C, B -> D, C -> D
    with open(jail_dir / "d.yaml", "w") as f:
        f.write("val: d")
    with open(jail_dir / "b.yaml", "w") as f:
        f.write('d: {"$ref": "d.yaml"}')
    with open(jail_dir / "c.yaml", "w") as f:
        f.write('d: {"$ref": "d.yaml"}')
    with open(jail_dir / "a.yaml", "w") as f:
        f.write('b: {"$ref": "b.yaml"}\nc: {"$ref": "c.yaml"}')

    data = loader.load(jail_dir / "a.yaml")
    assert data["b"]["d"]["val"] == "d"
    assert data["c"]["d"]["val"] == "d"

def test_hashing() -> None:
    # 1. Canonicalization
    data1 = {"b": 2, "a": 1}
    data2 = {"a": 1, "b": 2}
    assert canonicalize(data1) == canonicalize(data2)

    # Float handling
    assert canonicalize({"val": 20.0}) == b'{"val":20}'
    assert canonicalize({"val": 20.5}) == b'{"val":20.5}'

    # 2. Integrity Hash
    entry = {"user": "alice", "action": "login", "integrity_hash": "ignore_me"}
    h = compute_integrity_hash(entry)
    assert h == compute_integrity_hash({"user": "alice", "action": "login"})

    # 3. Chain Verification
    entry1 = {"id": 1, "data": "genesis", "previous_hash": None}
    h1 = compute_integrity_hash(entry1)
    entry1["integrity_hash"] = h1

    entry2 = {"id": 2, "data": "next", "previous_hash": h1}
    h2 = compute_integrity_hash(entry2)
    entry2["integrity_hash"] = h2

    chain = [entry1, entry2]
    assert verify_chain(chain)

    # Tamper
    entry1["data"] = "hacked"
    assert not verify_chain(chain)

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

    # Invalid edge
    builder.connect("agent1", "missing_node")
    with pytest.raises(ValueError, match="Edge target 'missing_node' not found"):
        builder.build()

    # Valid build
    # Remove invalid edge
    builder._edges.pop()
    flow = builder.build()

    # 2. Diff
    builder2 = NewGraphFlow("test_flow", "1.1", "Test")
    builder2.define_profile("profile1", "assistant", "helpful")  # Same profile
    builder2.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    builder2.add_agent_ref("agent1", "profile1")
    builder2.connect("switch1", "agent1")

    # Add new node and connect it to avoid orphan warning
    builder2.add_inspector("insp1", "target", "crit", "out")
    builder2.connect("agent1", "insp1")

    flow2 = builder2.build()

    changes = compare_manifests(flow, flow2)
    assert len(changes) > 0
    # Should see FEATURE for insp1
    features = [c for c in changes if c.category == ChangeCategory.FEATURE]
    assert len(features) == 1
    assert features[0].path == "graph.nodes.insp1"

    # Test Resource Change
    builder3 = NewGraphFlow("test_flow", "1.2", "Test")
    # Change profile model
    builder3.add_computer_use("profile1", "assistant", "helpful", "gpt-4-computer")
    builder3.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    builder3.add_agent_ref("agent1", "profile1")
    builder3.connect("switch1", "agent1")
    flow3 = builder3.build()

    changes3 = compare_manifests(flow, flow3)
    resources = [c for c in changes3 if c.category == ChangeCategory.RESOURCE]
    assert len(resources) == 1
    assert resources[0].path == "definitions.profiles.profile1.reasoning.model"
