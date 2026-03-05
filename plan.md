1. **Step 1: O(1) Hash Memoization (`src/coreason_manifest/core/base.py`)**
   - Update `__hash__` method to return `getattr(self, "_cached_hash")`.
   - Implement `model_post_init` using `object.__setattr__(self, "_cached_hash", hash(self.model_dump_canonical()))`.

2. **Step 2: Causal Physics Validators (Repository-Wide)**
   - Add `@model_validator(mode="after")` check to `ExecutionSpan` (`src/coreason_manifest/telemetry/schemas.py`) for `end_time_unix_nano >= start_time_unix_nano`.
   - Add `@model_validator(mode="after")` check to `DistributionProfile` (`src/coreason_manifest/compute/stochastic.py`) for `interval[0] < interval[1]`.
   - Add `@model_validator(mode="after")` check to `TemporalBounds` (`src/coreason_manifest/state/semantic.py`) for `valid_to >= valid_from`.

3. **Step 3: LLM DoS Bulkheads (Repository-Wide)**
   - Add `max_length=1000` to list fields:
     - `EpistemicLedger.history` (in `src/coreason_manifest/state/memory.py` - we'll set it to 10000 based on prompt hint).
     - We will update `ArgumentGraph` dictionary sizes `claims` and `attacks` setting `max_length=10000` on the dict.
     - `ExecutionSpan.events` -> `max_length=5000`.
   - Add `max_length=50000` to heavy text fields:
     - `InsightCard.markdown_content` (in `src/coreason_manifest/presentation/scivis.py`).
     - `ArgumentClaim.text_chunk` (in `src/coreason_manifest/state/argumentation.py`).
     - `SemanticNode.text_chunk` (in `src/coreason_manifest/state/semantic.py`).

4. **Step 4: Fuzzer Alignment (`tests/test_fuzzing.py`)**
   - Define custom strategies to align with the rules (e.g. `draw_temporal_bounds`).
   - Find all `st.lists(...)` and update with `max_size=100`.
   - Rewrite `draw_distribution_profile()` to enforce `interval[0] < interval[1]`.
   - Rewrite `draw_execution_span()` to draw `end_time_unix_nano` as `start_time_unix_nano + st.integers(min_value=0)`.
   - Use `st.composite` for `temporal_bounds` to draw `valid_from` + `delta`. Update the test decorators in `test_fuzzing.py` for `test_semanticnode_fuzzing` and `test_semanticedge_fuzzing` to use this new strategy.

5. **Step 5: Pre-commit Steps and Submission**
   - Pre-commit steps to make sure proper testing, verifications, reviews and reflections are done.
