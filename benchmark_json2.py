import canonicaljson
import msgspec

payload = {"a": 1, "b": "string", "c": [1, 2, 4], "d": {"e": 5, "g": [7]}}

encoder = msgspec.json.Encoder(order="deterministic")

c = canonicaljson.encode_canonical_json(payload)
m = encoder.encode(payload)

print(f"canonicaljson: {c}")
print(f"msgspec: {m}")
print(f"Match: {c == m}")
