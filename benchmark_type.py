import timeit


def _canonicalize_payload_isinstance(payload: any) -> any:
    if isinstance(payload, dict):
        return {k: _canonicalize_payload_isinstance(v) for k, v in payload.items() if v is not None}
    if isinstance(payload, list):
        return [_canonicalize_payload_isinstance(v) for v in payload if v is not None]
    return payload


def _canonicalize_payload_type(payload: any) -> any:
    ptype = type(payload)
    if ptype is dict:
        return {k: _canonicalize_payload_type(v) for k, v in payload.items() if v is not None}
    if ptype is list:
        return [_canonicalize_payload_type(v) for v in payload if v is not None]
    return payload


payload = {"a": 1, "b": None, "c": [1, 2, None, 4], "d": {"e": 5, "f": None, "g": [None, None, 7]}}

t_isinstance = timeit.timeit(lambda: _canonicalize_payload_isinstance(payload), number=100000)
t_type = timeit.timeit(lambda: _canonicalize_payload_type(payload), number=100000)

print(f"isinstance: {t_isinstance:.4f}s")
print(f"type: {t_type:.4f}s")
