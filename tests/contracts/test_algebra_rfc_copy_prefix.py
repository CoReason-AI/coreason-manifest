import os
import sys

import pytest

sys.path.insert(0, os.path.abspath("src"))
from coreason_manifest.spec.ontology import StateDifferentialManifest, StateMutationIntent
from coreason_manifest.utils.algebra import apply_state_differential


def test_copy_prefix() -> None:
    manifest = StateDifferentialManifest(
        diff_id="test",
        author_node_id="author",
        lamport_timestamp=1,
        vector_clock={},
        patches=[StateMutationIntent(op="copy", path="/a/b", **{"from": "/a"})],
    )
    current_state = {"a": {"x": 1}}
    with pytest.raises(ValueError, match="MUST NOT be a proper prefix"):
        apply_state_differential(current_state, manifest)


test_copy_prefix()
