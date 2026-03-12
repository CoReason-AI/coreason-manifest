import pytest
from coreason_manifest.utils.algebra import apply_state_differential
from coreason_manifest.spec.ontology import StateDifferentialManifest, StateMutationIntent

def test_apply_state_differential_add_dict():
    current_state = {"a": 1}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="add", path="/b", value=2)]
    )
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": 1, "b": 2}
    assert current_state == {"a": 1}

def test_apply_state_differential_add_list_append():
    current_state = {"a": [1, 2]}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="add", path="/a/-", value=3)]
    )
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": [1, 2, 3]}

def test_apply_state_differential_add_list_insert():
    current_state = {"a": [1, 2]}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="add", path="/a/0", value=0)]
    )
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": [0, 1, 2]}

def test_apply_state_differential_remove_dict():
    current_state = {"a": 1, "b": 2}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="remove", path="/b")]
    )
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": 1}

def test_apply_state_differential_remove_list():
    current_state = {"a": [1, 2, 3]}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="remove", path="/a/1")]
    )
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": [1, 3]}

def test_apply_state_differential_replace_dict():
    current_state = {"a": 1}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="replace", path="/a", value=2)]
    )
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": 2}

def test_apply_state_differential_replace_list():
    current_state = {"a": [1, 2, 3]}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="replace", path="/a/1", value=4)]
    )
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": [1, 4, 3]}

def test_apply_state_differential_move():
    current_state = {"a": {"b": 1}, "c": {}}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="move", **{"from": "/a/b", "path": "/c/b"})]
    )
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": {}, "c": {"b": 1}}

def test_apply_state_differential_copy():
    current_state = {"a": {"b": 1}, "c": {}}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="copy", **{"from": "/a/b", "path": "/c/b"})]
    )
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": {"b": 1}, "c": {"b": 1}}

def test_apply_state_differential_test_success():
    current_state = {"a": 1}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="test", path="/a", value=1)]
    )
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": 1}

def test_apply_state_differential_test_fail():
    current_state = {"a": 1}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="test", path="/a", value=2)]
    )
    with pytest.raises(ValueError, match="Patch test operation failed."):
        apply_state_differential(current_state, manifest)

def test_apply_state_differential_test_fail_root():
    current_state = {"a": 1}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="test", path="", value={"a": 2})]
    )
    with pytest.raises(ValueError, match="Patch test operation failed."):
        apply_state_differential(current_state, manifest)

def test_apply_state_differential_test_success_root():
    current_state = {"a": 1}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="test", path="", value={"a": 1})]
    )
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": 1}

def test_apply_state_differential_invalid_op_root():
    current_state = {"a": 1}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="add", path="", value={"a": 1})]
    )
    with pytest.raises(ValueError, match="Invalid path or root operation not supported"):
        apply_state_differential(current_state, manifest)

def test_apply_state_differential_invalid_pointer():
    current_state = {"a": 1}
    manifest = StateDifferentialManifest(diff_id="id", author_node_id="node", lamport_timestamp=1, vector_clock={},
        patches=[StateMutationIntent(op="add", path="invalid", value=1)]
    )
    with pytest.raises(ValueError, match="Invalid JSON pointer"):
        apply_state_differential(current_state, manifest)
