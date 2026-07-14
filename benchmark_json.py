import timeit

import canonicaljson
import msgspec

payload = {"a": 1, "b": "string", "c": [1, 2, 4], "d": {"e": 5, "g": [7]}}

encoder = msgspec.json.Encoder(order="deterministic")


def serialize_canonicaljson():
    return canonicaljson.encode_canonical_json(payload)


def serialize_msgspec():
    return encoder.encode(payload)


t_canonical = timeit.timeit(serialize_canonicaljson, number=100000)
t_msgspec = timeit.timeit(serialize_msgspec, number=100000)

print(f"canonicaljson: {t_canonical:.4f}s")
print(f"msgspec: {t_msgspec:.4f}s")
