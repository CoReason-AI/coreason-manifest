from pathlib import Path
from typing import Any

import pytest

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
            f.write(f'next: {{"$ref": "depth_{i + 1}.yaml"}}')
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
        canonicalize({"val": float("inf")})

    # 2. Integrity Hash (Aliases)
    class MockModel:
        def model_dump(self, _mode: str, by_alias: bool = False) -> dict[str, Any]:
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
    builder.define_profile("profile1", "assistant", "helpful")
    builder.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    builder.add_agent_ref("agent1", "profile1", tools=["search"])
    builder.connect("switch1", "agent1")

    flow = builder.build()

    # 2. Diff (Agent Tool Change)
    builder2 = NewGraphFlow("test_flow", "1.1", "Test")
    builder2.define_profile("profile1", "assistant", "helpful")
    builder2.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    # Change tools: remove "search", add "calculator"
    builder2.add_agent_ref("agent1", "profile1", tools=["calculator"])
    builder2.connect("switch1", "agent1")

    flow2 = builder2.build()

    changes = compare_manifests(flow, flow2)

    # Should see BREAKING for removed tool "search"
    breaking = [c for c in changes if c.category == ChangeCategory.BREAKING and c.path == "graph.nodes.agent1.tools"]
    assert len(breaking) == 1
    assert breaking[0].old == ["search"]

    # Should see FEATURE for added tool "calculator"
    features = [c for c in changes if c.category == ChangeCategory.FEATURE and c.path == "graph.nodes.agent1.tools"]
    assert len(features) == 1
    assert features[0].new == ["calculator"]

    # 3. Diff (Inspector Criteria)
    builder3 = NewGraphFlow("test_flow", "1.2", "Test")
    # ... setup flow3 with inspector change ...
    builder3.add_inspector(
        "insp1", "target", "strict", "out"
    )  # Old was implicit None? No, let's create a base flow with inspector
    # Let's create a new base flow for inspector test
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
    builder3.define_profile("profile1", "assistant", "helpful")
    builder3.add_computer_use("profile1", "assistant", "helpful", "gpt-4-computer")  # Model change
    # Note: profile1 in flow (builder 1) had no reasoning (StandardReasoning default is None in add_agent_ref? No, add_agent_ref uses profile_id reference.
    # builder.define_profile("profile1", ...) creates CognitiveProfile.
    # By default reasoning is None.
    # builder3.add_computer_use overwrites profile1 with ComputerUseReasoning.
    # old=None, new=ComputerUseReasoning. model change detected?
    # Logic: if old_m != new_m -> RESOURCE.
    # old_m is None. new_m is "gpt-4-computer".

    # We need to construct a flow where profile is used.
    builder3.add_switch("switch1", "var1", {"case1": "agent1"}, "agent1")
    builder3.add_agent_ref("agent1", "profile1")
    builder3.connect("switch1", "agent1")
    flow3 = builder3.build()

    changes3 = compare_manifests(flow, flow3)
    resources = [c for c in changes3 if c.category == ChangeCategory.RESOURCE]
    assert len(resources) == 1
    assert resources[0].path == "definitions.profiles.profile1.reasoning.model"


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
