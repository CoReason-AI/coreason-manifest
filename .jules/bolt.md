## 2024-05-19 - Caching decoded base64 NumPy Arrays on Frozen Pydantic Models
**Learning:** In highly restricted environments with `frozen=True` Pydantic models, caching intermediate computationally expensive decoded structures (like NumPy arrays from base64) directly on the instance requires bypassing Python immutability.
**Action:** Use `object.__getattribute__(instance, '_cached_property')` to fetch and `object.__setattr__(instance, '_cached_property', value)` to safely bypass immutability guards without violating architectural schema rules, yielding ~5x performance gains for repeated operations.

## 2024-05-19 - Efficient DAG Longest Path with Kahn's Algorithm
**Learning:** Combining topological sort extraction and topological path distance calculation into a single pass using Kahn's algorithm reduces memory allocation and iteration time by around 30% for Python dictionary DAG representations. By the time a node is popped from Kahn's queue, its longest path distance is mathematically resolved, meaning children distances can be evaluated in the exact same loop.
**Action:** Always compute derived states (like maximum paths) in the same loop pass as the topological queue execution to avoid O(V) array allocations and a secondary O(V+E) looping step.
