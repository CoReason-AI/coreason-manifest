## 2024-05-18 - NumPy Array Norm Calculation

**Learning:** Replacing `np.linalg.norm` with `math.sqrt(np.dot(arr1, arr1))` for 1D arrays is significantly faster (~35%) because it avoids NumPy's internal multi-dimensional checks and broadcasting overheads.

**Action:** When calculating the magnitude or norm of known 1D arrays in performance-critical code (like calculating vector similarity), prefer `math.sqrt(np.dot(v, v))` over `np.linalg.norm(v)`.

## 2024-05-18 - Replacing canonicaljson with msgspec

**Learning:** `canonicaljson.encode_canonical_json` is significantly slower than `msgspec.json.Encoder(order="deterministic")`. In `coreason_manifest`, replacing the usage of `canonicaljson` in the `ontology.py` module with `msgspec` provides an order of magnitude speedup for serialization and hashing, without compromising deterministic requirements (RFC 8785).

**Action:** Whenever deterministic serialization is needed and `msgspec` is available or acceptable, prefer it over `canonicaljson` for performance. Cache the `msgspec.json.Encoder` instance for maximum performance.

## 2026-04-25 - Copy deepcopy optimization on large dictionaries
**Learning:** `copy.deepcopy()` is extremely slow for complex, deeply nested JSON-serializable structures. The initial attempt to optimize via `msgspec` caused a runtime dependency issue.
**Action:** Always prefer Python's built-in `json.loads` over `copy.deepcopy()` when returning safe, decoupled deep copies of JSON-safe data (like Pydantic JSON schemas) to achieve a massive performance boost natively without breaking dependency boundaries.
