import json
from datetime import datetime, timezone, timedelta
from coreason_manifest.utils.integrity import compute_hash, to_canonical_timestamp

def test_canonical_timestamp():
    dt_utc = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    dt_offset = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone(timedelta(hours=1)))

    # Verify they represent the same instant
    assert dt_utc == dt_offset

    # Verify canonical string is identical
    s1 = to_canonical_timestamp(dt_utc)
    s2 = to_canonical_timestamp(dt_offset)
    assert s1 == "2023-01-01T12:00:00Z"
    assert s1 == s2

def test_hash_determinism_timezones():
    dt_utc = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    dt_offset = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone(timedelta(hours=1)))

    obj1 = {"created_at": dt_utc}
    obj2 = {"created_at": dt_offset}

    h1 = compute_hash(obj1)
    h2 = compute_hash(obj2)

    assert h1 == h2

def test_hash_determinism_key_order():
    obj1 = {"a": 1, "b": {"x": 10, "y": 20}}
    obj2 = {"b": {"y": 20, "x": 10}, "a": 1}

    h1 = compute_hash(obj1)
    h2 = compute_hash(obj2)

    assert h1 == h2

def test_hash_exclude_none():
    obj1 = {"a": 1, "b": None}
    obj2 = {"a": 1}

    h1 = compute_hash(obj1)
    h2 = compute_hash(obj2)

    assert h1 == h2
