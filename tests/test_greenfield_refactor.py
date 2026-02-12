from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from coreason_manifest.utils.integrity import compute_hash, verify_merkle_proof
from coreason_manifest.utils.loader import CitadelLoader, SecurityError


def test_citadel_loader_basic() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "main.yaml").write_text("kind: LinearFlow\nsequence: []")

        loader = CitadelLoader(root)
        data = loader.load_file(root / "main.yaml")
        assert data["kind"] == "LinearFlow"


def test_citadel_loader_jailbreak() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        jail = root / "jail"
        jail.mkdir()
        outside = root / "outside.yaml"
        outside.write_text("secret: true")

        (jail / "exploit.yaml").write_text('$ref: "../outside.yaml"')

        loader = CitadelLoader(jail)

        # Test direct load outside jail
        with pytest.raises(SecurityError):
            loader.load_file(outside)

        # Test ref outside jail
        with pytest.raises(SecurityError):
            loader.load_file(jail / "exploit.yaml")


def test_citadel_loader_recursion() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "part.yaml").write_text("value: 42")
        (root / "main.yaml").write_text("data: { $ref: 'part.yaml' }")

        loader = CitadelLoader(root)
        data = loader.load_file(root / "main.yaml")
        assert data["data"]["value"] == 42


def test_node_execution_schema() -> None:
    # Valid new schema
    node = NodeExecution(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={},
        outputs={},
        timestamp=datetime.now(),
        duration_ms=100.0,
        previous_hashes=["abc"],
    )
    assert node.previous_hashes == ["abc"]

    # Check default empty list
    node2 = NodeExecution(
        node_id="n2",
        state=NodeState.COMPLETED,
        inputs={},
        outputs={},
        timestamp=datetime.now(),
        duration_ms=100.0,
    )
    assert node2.previous_hashes == []

    # Check forbidden previous_hash
    with pytest.raises(ValidationError):
        NodeExecution(
            node_id="n3",
            state=NodeState.COMPLETED,
            inputs={},
            outputs={},
            timestamp=datetime.now(),
            duration_ms=100.0,
            previous_hash="abc",  # type: ignore # Should fail extra="forbid"
        )


def test_verify_merkle_dag() -> None:
    # Construct a valid DAG chain
    # Node 1 (Genesis)
    n1 = {"id": "1", "previous_hashes": []}
    h1 = compute_hash(n1)

    # Node 2 (Linear)
    n2 = {"id": "2", "previous_hashes": [h1]}
    h2 = compute_hash(n2)

    # Node 3 (Branch A)
    n3 = {"id": "3", "previous_hashes": [h2]}
    h3 = compute_hash(n3)

    # Node 4 (Branch B)
    n4 = {"id": "4", "previous_hashes": [h2]}
    h4 = compute_hash(n4)

    # Node 5 (Merge)
    n5 = {"id": "5", "previous_hashes": [h3, h4]}

    chain = [n1, n2, n3, n4, n5]
    assert verify_merkle_proof(chain)

    # Invalid: Missing hash
    n_bad = {"id": "bad", "previous_hashes": ["invalid_hash"]}
    assert not verify_merkle_proof([n1, n_bad])

    # Invalid: Disconnected (empty previous_hashes for non-genesis)
    n_disconnected = {"id": "disc", "previous_hashes": []}
    assert not verify_merkle_proof([n1, n_disconnected])


def test_citadel_loader_missing_ref() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "main.yaml").write_text("data: { $ref: 'missing.yaml' }")

        loader = CitadelLoader(root)
        with pytest.raises(FileNotFoundError, match="Referenced file not found"):
            loader.load_file(root / "main.yaml")


def test_citadel_loader_invalid_ref_type() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "main.yaml").write_text("data: { $ref: 123 }")

        loader = CitadelLoader(root)
        with pytest.raises(ValueError, match=r"Invalid \$ref value"):
            loader.load_file(root / "main.yaml")
