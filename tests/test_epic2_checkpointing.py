import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core import Blackboard, Checkpoint, PersistenceConfig, StateDiff


def test_persistence_config_success() -> None:
    config = PersistenceConfig(backend_type="redis", ttl_seconds=3600)
    assert config.backend_type == "redis"  # noqa: S101
    assert config.ttl_seconds == 3600  # noqa: S101

    # TTL is optional
    config2 = PersistenceConfig(backend_type="s3")
    assert config2.backend_type == "s3"  # noqa: S101
    assert config2.ttl_seconds is None  # noqa: S101


def test_persistence_config_failure() -> None:
    # Invalid backend type
    with pytest.raises(ValidationError):
        PersistenceConfig(backend_type="invalid_backend")  # type: ignore

    # Negative TTL
    with pytest.raises(ValidationError):
        PersistenceConfig(backend_type="redis", ttl_seconds=-1)


def test_state_diff_success() -> None:
    diff = StateDiff(op="add", path="/foo", value="bar")
    assert diff.op == "add"  # noqa: S101
    assert diff.path == "/foo"  # noqa: S101
    assert diff.value == "bar"  # noqa: S101

    # Move op with from_ alias
    diff2 = StateDiff(op="move", path="/foo", **{"from": "/bar"})  # type: ignore
    assert diff2.op == "move"  # noqa: S101
    assert diff2.from_ == "/bar"  # noqa: S101


def test_state_diff_failure() -> None:
    # Invalid op
    with pytest.raises(ValidationError):
        StateDiff(op="invalid_op", path="/foo")  # type: ignore


def test_checkpoint_success() -> None:
    cp = Checkpoint(
        thread_id="thread-123",
        node_id="node-abc",
        state_diff=[StateDiff(op="add", path="/state/val1", value=42), StateDiff(op="remove", path="/state/val2")],
    )
    assert cp.thread_id == "thread-123"  # noqa: S101
    assert cp.node_id == "node-abc"  # noqa: S101
    assert len(cp.state_diff) == 2  # noqa: S101


def test_checkpoint_failure() -> None:
    # Missing required field
    with pytest.raises(ValidationError):
        Checkpoint(thread_id="thread-123", state_diff=[])  # type: ignore


def test_blackboard_persistence_override() -> None:
    bb = Blackboard(persistence=PersistenceConfig(backend_type="postgres"))
    assert bb.persistence is not None  # noqa: S101
    assert bb.persistence.backend_type == "postgres"  # noqa: S101

    # Persistence is optional
    bb2 = Blackboard()
    assert bb2.persistence is None  # noqa: S101

    # Invalid persistence config
    with pytest.raises(ValidationError):
        Blackboard(persistence={"backend_type": "invalid"})  # type: ignore
