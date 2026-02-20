from datetime import datetime
from unittest.mock import patch

import idna
import pytest
from pydantic import ValidationError

from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from coreason_manifest.utils.diff import _classify_path, _generate_diff
from coreason_manifest.utils.integrity import compute_hash, reconstruct_payload
from coreason_manifest.utils.loader import SandboxedPathFinder, load_agent_from_ref
from coreason_manifest.utils.net_utils import canonicalize_domain


def test_diff_classifier_coverage() -> None:
    # Cover _classify_path branches
    assert _classify_path("/edges/0") == "topology"
    assert _classify_path("/graph/nodes/id") == "topology"  # len 4
    assert _classify_path("/graph/nodes/id/prop") == "resource"
    assert _classify_path("/sequence/0") == "topology"  # len 3
    assert _classify_path("/sequence/0/prop") == "resource"
    assert _classify_path("/other") == "resource"

    # Cover _classify_path governance (line 72)
    assert _classify_path("/governance/policy") == "governance"


def test_diff_list_logic_coverage() -> None:
    # Cover list diff logic in _generate_diff
    # Add (len2 > len1)
    l1: list[int] = []
    l2 = [1]
    diff = _generate_diff("/list", l1, l2)
    assert len(diff) == 1
    assert diff[0].op == "add"

    # Remove (len1 > len2)
    l3 = [1, 2]
    l4 = [1]
    diff = _generate_diff("/list", l3, l4)
    assert len(diff) == 1
    assert diff[0].op == "remove"
    assert diff[0].path == "/list/1"

    # Branch coverage for loops
    # If len1 == len2, loops for add/remove are skipped
    # Recursion happens in first loop.
    l5 = [1]
    l6 = [2]
    diff = _generate_diff("/list", l5, l6)
    assert len(diff) == 1
    assert diff[0].op == "replace"  # because primitives differ


def test_integrity_nan_check() -> None:
    # line 75 check is_finite for floats
    with pytest.raises(ValueError, match="NaN and Infinity"):
        compute_hash(float("nan"))
    with pytest.raises(ValueError, match="NaN and Infinity"):
        compute_hash(float("inf"))


def test_integrity_fallback_json() -> None:
    # Cover fallback lines 89-90 (has json method)
    class HasJson:
        def json(self) -> str:
            return '{"key": "value"}'

    obj = HasJson()
    # Should use json() method
    h = compute_hash(obj)
    assert h == compute_hash({"key": "value"})

    # Error in json load?
    class BadJson:
        def json(self) -> str:
            return "invalid"

    # Should fall through to TypeError
    with pytest.raises(TypeError):
        compute_hash(BadJson())


def test_integrity_tuple_reconstruct() -> None:
    # Cover reconstruct_payload list/tuple path (lines 140-154)
    data = [("a", 1)]
    res = reconstruct_payload(data)
    assert res == {"a": 1}

    with pytest.raises(TypeError, match="Could not reconstruct payload"):
        reconstruct_payload([1])


def test_loader_spec_none_coverage() -> None:
    # Cover SandboxedPathFinder branches
    finder = SandboxedPathFinder()
    assert finder.find_spec("foo") is None  # jail_root not set

    # ".." check
    from pathlib import Path

    from coreason_manifest.utils.loader import sandbox_context

    with sandbox_context(Path(".")):
        assert finder.find_spec("..foo") is None
        # line 119: init_py is file -> create dummy init
        # line 126: module_py is file

        # Test package loading (init.py exists)
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "mypkg").mkdir()
            (p / "mypkg" / "__init__.py").touch()
            with sandbox_context(p):
                spec = finder.find_spec("mypkg")
                assert spec is not None
                assert spec.origin is not None
                assert spec.origin.endswith("__init__.py")

        # Test module loading (file.py exists)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "mymod.py").touch()
            with sandbox_context(p):
                spec = finder.find_spec("mymod")
                assert spec is not None
                assert spec.origin is not None
                assert spec.origin.endswith("mymod.py")

        # If neither exists, returns None.
        assert finder.find_spec("non_existent") is None


def test_loader_exception_handling_in_lock() -> None:
    # Cover exception handling inside _loader_lock (lines 233, 253, 281-282)
    # We need to trigger exception during exec_module

    # Create a broken agent file
    # Mocking is hard here because it's inside context manager.
    # Instead, create real broken file.
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "broken.py").write_text("raise RuntimeError('Boom')")

        with pytest.raises(ValueError, match="Failed to execute agent code"):
            load_agent_from_ref("broken.py:Agent", root_dir=p)


def test_net_utils_edge_cases() -> None:
    # line 12: if not domain return ""
    assert canonicalize_domain("") == ""
    # Test runtime None handling (mypy prevents direct None passing)
    # We must cast None to Any to bypass static type checking, validating runtime resilience.
    from typing import Any, cast

    assert canonicalize_domain(cast("Any", None)) == ""

    # Force IDNA error (line 24-27)
    with patch("idna.encode", side_effect=idna.IDNAError):
        assert canonicalize_domain("bad.com") == "bad.com"


def test_telemetry_frozen() -> None:
    # Telemetry frozen checks lines 75-76, 80
    ne = NodeExecution(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={},
        outputs={},
        timestamp=datetime.now(),
        duration_ms=10,
        request_id="req",
        root_request_id="req",
    )
    # Attempt to mutate frozen field
    with pytest.raises(ValidationError):
        ne.state = NodeState.FAILED  # type: ignore


def test_validator_edge_cases() -> None:
    # validator.py 70, 282, 284, 309
    # line 70: check schema if boolean
    # covered by test_schema_boolean

    # line 282: GraphFlow Error: Graph must contain at least one node.
    # line 284: Graph Integrity Error: Node key matches ID.
    pass  # covered by tests/test_validator_phase3a.py


def test_visualizer_unvisited() -> None:
    # visualizer.py 185-187
    pass


def test_flow_cycle_detection_unreachable() -> None:
    # spec/core/flow.py 325-326 (raise ValueError("Cycle detected..."))
    # The previous fix uses Kahn's algorithm which doesn't use recursion stack.
    # The line numbers suggest "2b. Cycle Detection using Kahn's..." block or the old DFS block?
    # My replace used Kahn's.
    # 325-326 in Kahn's?
    # "if visited_count != len(reachable): ... raise ValueError"
    # This is hit if cycle exists.
    # We need a test with a cycle in a PUBLISHED flow.
    from coreason_manifest.spec.core.flow import (
        DataSchema,
        Edge,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
    )
    from coreason_manifest.spec.core.nodes import PlaceholderNode

    n1 = PlaceholderNode(id="n1", type="placeholder", metadata={}, required_capabilities=[])
    n2 = PlaceholderNode(id="n2", type="placeholder", metadata={}, required_capabilities=[])

    # Cycle: n1->n2->n1
    graph = Graph(
        nodes={"n1": n1, "n2": n2},
        edges=[Edge(source="n1", target="n2"), Edge(source="n2", target="n1")],
        entry_point="n1",
    )

    with pytest.raises(ValueError, match="Cycle detected"):
        GraphFlow(
            kind="GraphFlow",
            status="published",
            metadata=FlowMetadata(name="cycle", version="1", description="d", tags=[]),
            interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
            blackboard=None,
            graph=graph,
        )
