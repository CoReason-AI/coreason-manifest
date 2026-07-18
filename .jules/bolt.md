
## 2025-03-09 - Faster canonicalize via type equality
**Learning:** Checking `type(x) is dict` instead of `isinstance(x, dict)` is roughly 20-25% faster for extremely deep/large recursive payloads on Python. `_canonicalize_payload` runs hundreds of times per serialization, so avoiding the metaclass/MRO checks in `isinstance` yields a measurable speedup.
**Action:** Use `type(x) is dict` or `type(x) is list` for hot-path recursive traversals if we know that subclasses aren't being used in that codepath.
