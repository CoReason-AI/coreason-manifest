## 2025-07-12 - Reusing msgspec Encoder in DeterministicTransportAdapter
**Learning:** `msgspec.json.Encoder` instantiation has overhead that becomes noticeable in high-throughput serialization paths (like the MCP transport adapter here). It is safe to hoist the encoder to the class level since its configuration is static and thread-safe.
**Action:** When using `msgspec` encoders for deterministic serialization, prefer caching and reusing them rather than recreating them per payload.
