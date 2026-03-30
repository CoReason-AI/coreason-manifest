## 2025-02-17 - Eliminate redundant Python-level sorting for canonical JSON
**Learning:** For producing canonically sorted JSON via Pydantic model dicts, traversing nested dicts/lists to sort the keys of dictionary items in Python is redundant and computationally expensive if `json.dumps(..., sort_keys=True)` is used on the resulting dict. Natively, `json.dumps` with `sort_keys=True` already guarantees all keys of all nested objects are recursively sorted during serialization, yielding the exact same output much faster.
**Action:** Do not manually sort dictionary keys before passing them into `json.dumps` if `sort_keys=True` can be leveraged instead. Keep the sorting at the C-level serialization layer where it is significantly more optimized.

## 2025-02-18 - Optimize list popping for queues
**Learning:** Using `list.pop(0)` for a queue in Kahn's algorithm (or any queue structure processing many elements) creates an $O(N)$ operation per element since all remaining list elements must shift. For large directed acyclic graphs, this cascades into an $O(N^2)$ algorithm instead of the intended $O(V+E)$.
**Action:** Always use `collections.deque` and its $O(1)$ `popleft()` method when implementing FIFO queues in algorithms to ensure optimal temporal complexity.

## 2025-02-19 - Eliminate static collection instantiation inside hot path functions
**Learning:** Re-defining static collections (like lists, tuples, dictionaries, and sets used as allowlists) inside a function causes Python to re-allocate and garbage-collect those objects on every function call. For functions called frequently, like `verify_ast_safety`, this creates an unnecessary $O(N)$ allocation bottleneck on each invocation.
**Action:** Extract static collections from function bodies into module-level constants (e.g., `_AST_ALLOWLIST: tuple[type, ...] = (...)`) and convert lists/sets to tuples or frozensets when mutability isn't required. This reduces per-call overhead and avoids redundant memory allocations.
## 2026-03-27 - [Caching Canonical Payload Serialization]
**Learning:** Pydantic's `model_dump(mode="json")` and `json.dumps()` serialization are inherently expensive, particularly on nested dictionary graphs and classes that undergo constant hashing checks. Since `CoreasonBaseState` strictly enforces `frozen=True` rendering models fully immutable upon creation, the result of `model_dump_canonical()` will never change for the entire lifecycle of an object.
**Action:** For heavily-hashed base structures where immutability is guaranteed at instantiation (`frozen=True`), cache the canonical byte payload natively using `object.__setattr__(self, "_cached_canonical_dump", canonical_dump)` inside `model_dump_canonical()`. This skips repetitive recursive serializations in subsequent calls, bypassing deep Pydantic validation boundaries on reads.

## 2026-03-30 - Caching Pydantic JSON Schema Generation
**Learning:** Generating JSON schema dynamically from a large set of Pydantic models using `models_json_schema` is computationally expensive because Pydantic has to perform deep reflection and loop through models each time it is called. When called repeatedly (e.g., in loops or CLI invocations), it creates a severe performance bottleneck.
**Action:** When a function computes a large schema deterministically from static module contents, decorate it with `@functools.lru_cache(maxsize=1)` so that the massive schema generation only happens once per process, drastically speeding up subsequent retrievals.
