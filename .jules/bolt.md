## 2026-04-25 - Copy deepcopy optimization on large dictionaries
**Learning:** `copy.deepcopy()` is extremely slow for complex, deeply nested JSON-serializable structures. The initial attempt to optimize via `msgspec` caused a runtime dependency issue.
**Action:** Always prefer Python's built-in `json.loads` over `copy.deepcopy()` when returning safe, decoupled deep copies of JSON-safe data (like Pydantic JSON schemas) to achieve a massive performance boost natively without breaking dependency boundaries.
