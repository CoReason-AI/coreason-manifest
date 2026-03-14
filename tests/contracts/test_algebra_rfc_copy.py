import os
import sys

sys.path.insert(0, os.path.abspath("src"))
from coreason_manifest.spec.ontology import StateDifferentialManifest, StateMutationIntent
from coreason_manifest.utils.algebra import apply_state_differential


def test_copy() -> None:
    manifest = StateDifferentialManifest(
        diff_id="test",
        author_node_id="author",
        lamport_timestamp=1,
        vector_clock={},
        patches=[StateMutationIntent(op="copy", path="/a/2", **{"from": "/a/0"})],
    )
    current_state = {"a": [1, 2, 3]}
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == {"a": [1, 2, 1, 3]}
