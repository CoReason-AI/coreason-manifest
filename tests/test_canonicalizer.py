import json

from coreason_manifest.utils.integrity import canonicalizer, compute_hash


def test_canonicalizer_compliance() -> None:
    # 1. Whitespace and ordering
    obj1 = {"b": 1, "a": 2}
    obj2 = {"a": 2, "b": 1}

    # Canonical form should be identical
    canon1 = canonicalizer.to_json(obj1)
    canon2 = canonicalizer.to_json(obj2)

    assert canon1 == canon2
    assert canon1 == b'{"a":2,"b":1}' # Strict check: no space after colon/comma

def test_canonicalizer_utf8() -> None:
    # 2. UTF-8 vs Unicode Escape
    obj = {"key": "ümldaüt"}
    canon = canonicalizer.to_json(obj)
    # Should not be \u00fc...
    assert b'\xc3\xbc' in canon # ü in utf-8
    assert b'\\u' not in canon

def test_canonicalizer_types() -> None:
    obj = {
        "float": 1.0, # Should be integer 1
        "null": None, # Should be stripped in dict (SOTA context) or null in list
        "list": [None, 1.5]
    }
    # My implementation strips None in dicts.
    canon = canonicalizer.to_json(obj)
    decoded = json.loads(canon)

    assert "null" not in decoded
    assert decoded["float"] == 1
    assert decoded["list"] == [None, 1.5] # List preserves None? My code:
    # if isinstance(obj, (list, tuple)): return [self._prepare_object(x) for x in obj]
    # _prepare_object(None) -> None.
    # json.dumps([None]) -> [null]. Yes.

def test_compute_hash_consistency() -> None:
    obj1 = {"a": 1, "b": [1, 2]}
    obj2 = {"b": [1, 2], "a": 1}
    assert compute_hash(obj1) == compute_hash(obj2)
