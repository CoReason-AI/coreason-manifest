import pytest
from pathlib import Path
from coreason_manifest.spec.core.flow import GraphFlow, FlowMetadata, FlowInterface, Graph, Edge, FlowDefinitions
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.engines import ComputerUseReasoning
from coreason_manifest.spec.core.governance import Governance, PolicyConfig
from coreason_manifest.utils.gatekeeper import validate_policy, PolicyViolation
from coreason_manifest.utils.integrity import create_merkle_node, verify_merkle_proof, compute_state_hash, MerkleNode
from coreason_manifest.utils.loader import CitadelLoader, safety_check

# =========================================================================
# GATEKEEPER COVERAGE
# =========================================================================

def test_gatekeeper_no_governance() -> None:
    # Line 23: if not flow.governance or not flow.governance.policy: return []
    graph = Graph(nodes={}, edges=[])
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="test", version="1.0", description="test", tags=[]),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph,
        governance=None
    )
    assert validate_policy(flow) == []

    # Create a new flow with governance but no policy
    flow_with_gov_no_policy = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="test", version="1.0", description="test", tags=[]),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph,
        governance=Governance(policy=None)
    )
    assert validate_policy(flow_with_gov_no_policy) == []

def test_gatekeeper_missing_profile_definition() -> None:
    # Lines 44-48: Profile is string but not in definitions
    # Use model_construct to bypass Pydantic validation which enforces referential integrity
    policy = PolicyConfig(allowed_capabilities=[], require_human_in_loop_for=[], max_risk_score=0.5)
    gov = Governance(policy=policy)

    node = AgentNode(
        id="agent1", type="agent", metadata={}, supervision=None,
        profile="missing_profile_id", tools=[]
    )
    graph = Graph(nodes={"agent1": node}, edges=[])

    flow = GraphFlow.model_construct(
        kind="GraphFlow",
        metadata=FlowMetadata(name="test", version="1.0", description="test", tags=[]),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph,
        governance=gov,
        definitions=FlowDefinitions(profiles={})
    )

    # Should not crash, just continue (and trigger the missing profile branch)
    assert validate_policy(flow) == []

def test_gatekeeper_resolved_profile_definition() -> None:
    # Coverage for gatekeeper.py line 44: profile = flow.definitions.profiles[profile]
    policy = PolicyConfig(allowed_capabilities=[], require_human_in_loop_for=[], max_risk_score=0.5)
    gov = Governance(policy=policy)

    # Profile defined in registry
    profile_def = CognitiveProfile(
        role="worker", persona="worker", reasoning=ComputerUseReasoning(model="gpt-4"), fast_path=None
    )

    # Node references ID
    node = AgentNode(
        id="agent1", type="agent", metadata={}, supervision=None,
        profile="profile_1", tools=[]
    )
    graph = Graph(nodes={"agent1": node}, edges=[])

    flow = GraphFlow.model_construct(
        kind="GraphFlow",
        metadata=FlowMetadata(name="test", version="1.0", description="test", tags=[]),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph,
        governance=gov,
        definitions=FlowDefinitions(profiles={"profile_1": profile_def})
    )

    # Should detect violations from the RESOLVED profile (which uses ComputerUse)
    violations = validate_policy(flow)
    assert len(violations) == 1
    assert violations[0].rule == "Capability Check"

# =========================================================================
# INTEGRITY COVERAGE
# =========================================================================

def test_integrity_sha512() -> None:
    # Lines 25-27, 38-40: SHA512 support
    blackboard = {"foo": "bar"}
    hash_512 = compute_state_hash(blackboard, algorithm="sha512")
    assert len(hash_512) == 128 # SHA512 hexdigest length

    node = create_merkle_node(["prev"], "node1", blackboard, algorithm="sha512")
    assert node.state_diff_hash == hash_512

    node_hash = node.compute_hash(algorithm="sha512")
    assert len(node_hash) == 128

def test_integrity_empty_chain() -> None:
    # Line 64: if not chain: return True
    assert verify_merkle_proof([]) is True

def test_integrity_invalid_algorithm() -> None:
    # Lines 30, 43: Unsupported algorithm
    blackboard = {"foo": "bar"}
    with pytest.raises(ValueError, match="Unsupported algorithm"):
        compute_state_hash(blackboard, algorithm="md5") # type: ignore

    node = create_merkle_node(["0"], "node", blackboard)
    with pytest.raises(ValueError, match="Unsupported algorithm"):
        node.compute_hash(algorithm="md5") # type: ignore

def test_integrity_multiple_roots() -> None:
    # Line 94: if prev_hash == "0": continue
    # Verify a chain with two independent roots (forest)
    root1 = create_merkle_node(["0"], "root1", {"a": 1})
    root2 = create_merkle_node(["0"], "root2", {"b": 2})

    # If verify_merkle_proof supports lists of disconnected nodes (which a DAG list might contain if topographically sorted)
    chain = [root1, root2]
    assert verify_merkle_proof(chain) is True

# =========================================================================
# LOADER COVERAGE
# =========================================================================

def test_loader_https_rejection(tmp_path: Path) -> None:
    # Lines 84-85: HTTPS rejection
    root = tmp_path / "app"
    root.mkdir()
    main = root / "main.yaml"
    main.write_text('$ref: "https://example.com/foo.yaml"', encoding="utf-8")

    loader = CitadelLoader(root=root, allow_https=False)
    with pytest.raises(ValueError, match="Remote references not allowed"):
        loader.load_recursive(main)

def test_loader_cache_hit(tmp_path: Path) -> None:
    # Line 121: Cache hit
    # Diamond dependency:
    # main -> a
    # main -> b
    # a -> c
    # b -> c (Should trigger cache hit for c)

    root = tmp_path / "app"
    root.mkdir()

    main = root / "main.yaml"
    a = root / "a.yaml"
    b = root / "b.yaml"
    c = root / "c.yaml"

    main.write_text("""
    part_a:
        $ref: "./a.yaml"
    part_b:
        $ref: "./b.yaml"
    """, encoding="utf-8")

    a.write_text('$ref: "./c.yaml"', encoding="utf-8")
    b.write_text('$ref: "./c.yaml"', encoding="utf-8")
    c.write_text("value: shared", encoding="utf-8")

    loader = CitadelLoader(root=root)
    result = loader.load_recursive(main)

    assert result["part_a"]["value"] == "shared"
    assert result["part_b"]["value"] == "shared"

def test_loader_missing_recursive_file(tmp_path: Path) -> None:
    # Line 124: if not abs_path.exists()
    root = tmp_path / "app"
    root.mkdir()
    main = root / "main.yaml"
    main.write_text('$ref: "./missing.yaml"', encoding="utf-8")

    loader = CitadelLoader(root=root)
    with pytest.raises(FileNotFoundError, match="Manifest file not found"):
        loader.load_recursive(main)

def test_loader_scalar_yaml(tmp_path: Path) -> None:
    # Line 138: if not isinstance(data, (dict, list))
    root = tmp_path / "app"
    root.mkdir()
    main = root / "main.yaml"
    main.write_text('"just a string"', encoding="utf-8")

    loader = CitadelLoader(root=root)
    result = loader.load_recursive(main)
    assert result == "just a string"
