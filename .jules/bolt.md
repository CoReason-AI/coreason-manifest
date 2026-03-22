## 2025-02-17 - Eliminate redundant Python-level sorting for canonical JSON
**Learning:** For producing canonically sorted JSON via Pydantic model dicts, traversing nested dicts/lists to sort the keys of dictionary items in Python is redundant and computationally expensive if `json.dumps(..., sort_keys=True)` is used on the resulting dict. Natively, `json.dumps` with `sort_keys=True` already guarantees all keys of all nested objects are recursively sorted during serialization, yielding the exact same output much faster.
**Action:** Do not manually sort dictionary keys before passing them into `json.dumps` if `sort_keys=True` can be leveraged instead. Keep the sorting at the C-level serialization layer where it is significantly more optimized.

## 2025-02-18 - Optimize list popping for queues
**Learning:** Using `list.pop(0)` for a queue in Kahn's algorithm (or any queue structure processing many elements) creates an $O(N)$ operation per element since all remaining list elements must shift. For large directed acyclic graphs, this cascades into an $O(N^2)$ algorithm instead of the intended $O(V+E)$.
**Action:** Always use `collections.deque` and its $O(1)$ `popleft()` method when implementing FIFO queues in algorithms to ensure optimal temporal complexity.
