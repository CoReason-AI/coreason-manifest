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

## 2026-03-27 - [Caching Dynamic Pydantic Schema Generation]
**Learning:** Generating JSON schemas at runtime using Pydantic's `models_json_schema(...)` is heavily unoptimized when the ontology graph is large (e.g., hundreds of nested `CoreasonBaseState` models). Calling it frequently acts as an O(N) structural traversal bottleneck, taking hundreds of milliseconds per invocation.
**Action:** Always cache the output of `models_json_schema(...)` at the module level (e.g., via a global `_CACHED_SCHEMA` variable) if the underlying ontology definitions are static during runtime. This provides an O(1) fast path on subsequent calls, dramatically reducing overhead.

## 2026-03-28 - [operator.attrgetter for C-level Sort Keys]
**Learning:** In heavily hashed immutable models using Pydantic, the `_enforce_canonical_sort` validator executes frequently. Using `lambda x: x.property` introduces significant Python function call overhead per element. Replacing `lambda` with `operator.attrgetter('property')` runs entirely in C, yielding a measurable 20-30% performance improvement on large collections.
**Action:** Always prefer `operator.attrgetter` over lambda functions for sort keys in hot loops or heavily repeated Pydantic model validation steps to guarantee optimal serialization throughput.
## 2026-03-29 - [Safe application of C-level sort operators]
**Learning:** While `operator.attrgetter` and `operator.itemgetter` are C-level optimizations that can replace slow lambdas, replacing `lambda x: str(x.value)` with `operator.attrgetter("value")` is dangerous. It changes the sorting logic from sorting by string representation to sorting by the raw value itself. This can cause TypeErrors or change the intended sort order.
**Action:** When converting lambdas to `operator` functions for performance, ensure the sorting semantics (like type casting) are strictly preserved. Do not convert lambdas that perform type casting (like `str()`) into pure attribute getters.
