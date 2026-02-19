from unittest.mock import patch

import idna
import pytest

from coreason_manifest.utils.diff import _classify_path, _generate_diff
from coreason_manifest.utils.integrity import compute_hash, reconstruct_payload
from coreason_manifest.utils.loader import SandboxedPathFinder
from coreason_manifest.utils.net_utils import canonicalize_domain


def test_diff_classifier_coverage() -> None:
    # Cover _classify_path branches
    assert _classify_path("/edges/0") == "topology"
    assert _classify_path("/graph/nodes/id") == "topology"  # len 4
    assert _classify_path("/graph/nodes/id/prop") == "resource"
    assert _classify_path("/sequence/0") == "topology"  # len 3
    assert _classify_path("/sequence/0/prop") == "resource"
    assert _classify_path("/other") == "resource"


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


def test_integrity_nan_check() -> None:
    with pytest.raises(ValueError, match="NaN and Infinity"):
        compute_hash(float("nan"))
    with pytest.raises(ValueError, match="NaN and Infinity"):
        compute_hash(float("inf"))


def test_integrity_tuple_reconstruct() -> None:
    # Cover reconstruct_payload list/tuple path (lines 140-154)
    # reconstruct_payload is mostly used for verification, expecting dict-like
    # If we pass a list of tuples, it converts to dict.
    data = [("a", 1)]
    res = reconstruct_payload(data)
    assert res == {"a": 1}

    # Test error path? "shouldn't happen with strict types"
    # If we pass something that fails dict conversion but is list/tuple
    # e.g. [1] (not pairs)
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


def test_net_utils_idna_error() -> None:
    # Force IDNA error
    with patch("idna.encode", side_effect=idna.IDNAError):
        # Should return original
        assert canonicalize_domain("bad.com") == "bad.com"


def test_telemetry_frozen() -> None:
    # Coverage for NodeExecution frozen check?
    # Usually pydantic handles this, but if there's a custom setattr...
    pass
