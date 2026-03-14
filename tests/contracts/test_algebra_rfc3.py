import os
import sys

import pytest

sys.path.insert(0, os.path.abspath("src"))
from coreason_manifest.spec.ontology import StateDifferentialManifest, StateMutationIntent
from coreason_manifest.utils.algebra import apply_state_differential


def test_move_exception_value_error() -> None:
    manifest = StateDifferentialManifest(
        diff_id="test",
        author_node_id="author",
        lamport_timestamp=1,
        vector_clock={},
        patches=[StateMutationIntent(op="move", path="/a/x", **{"from": "/a/2"})],
    )
    current_state = {"a": [1, 2, 3]}
    with pytest.raises(ValueError, match="Invalid index"):
        apply_state_differential(current_state, manifest)


test_move_exception_value_error()
