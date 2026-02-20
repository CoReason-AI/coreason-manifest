import pytest
from typing import Any, cast

from coreason_manifest.utils.resolver import CircularReferenceError, ResolutionContext


def test_dag_cycle_detection() -> None:
    # Mock loader
    mock_files: dict[str, Any] = {
        "a": {"$ref": "b"},
        "b": {"$ref": "a"},
    }

    def loader(uri: str) -> dict[str, Any]:
        return cast(dict[str, Any], mock_files[uri])

    ctx = ResolutionContext(loader)

    # Try resolving 'a'
    # resolve(a) -> refs b -> load b -> resolve(b) -> refs a -> check active -> ERROR

    with pytest.raises(CircularReferenceError) as excinfo:
        ctx.resolve(mock_files["a"], base_uri="root") # base_uri arbitrary here as we load by key

    # The path in error message depends on how we keyed it.
    # resolve(a) -> sees ref b. key=b. append b. load b.
    # resolve(b) -> sees ref a. key=a. append a. load a? No, we started with a manual call?
    # Wait, ctx.resolve(mock_files["a"], base_uri="root")
    # 'a' has {"$ref": "b"}.
    # It sees remote ref "b". Key="b".
    # _active_refs = ["b"].
    # Loads "b".
    # Recursive resolve(b_content, base_uri="b").
    # b_content has {"$ref": "a"}.
    # Sees remote ref "a". Key="a".
    # _active_refs = ["b", "a"].
    # Loads "a".
    # Recursive resolve(a_content, base_uri="a").
    # a_content has {"$ref": "b"}.
    # Sees remote ref "b". Key="b".
    # "b" is in _active_refs. Cycle!

    # Path: b -> a -> b
    assert "b -> a -> b" in str(excinfo.value)

def test_dag_diamond() -> None:
    # Diamond is fine: Root -> B, Root -> C, B -> D, C -> D
    # But here we test resolution
    mock_files: dict[str, Any] = {
        "root": {"b": {"$ref": "d"}, "c": {"$ref": "d"}},
        "d": {"val": 1}
    }

    call_count = 0
    def loader(uri: str) -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        return cast(dict[str, Any], mock_files[uri])

    ctx = ResolutionContext(loader)
    # Start resolving root content manually
    resolved = ctx.resolve(mock_files["root"], base_uri="root")

    assert resolved["b"] == {"val": 1}
    assert resolved["c"] == {"val": 1}
    assert call_count == 1 # Caching works! Loaded 'd' once.
