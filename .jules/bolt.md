## 2025-05-24 - [msgspec JSON Encoding]
**Learning:** canonicaljson is much slower than msgspec C-extension for deterministic JSON encoding. Reusing msgspec.json.Encoder(order="deterministic") instances globally rather than creating them on every call provides a significant serialization speedup.
**Action:** Always prefer globally cached msgspec encoders for high-performance deterministic serialization.
