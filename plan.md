1. **Inject `NetworkInterceptState` and `MemoryHeapSnapshot` in `ontology.py`**
   - Add new classes that inherit from `CoreasonBaseState`.
   - Add docstrings exactly as requested.
   - Define all fields with exact types, bounds, and string constraints as requested.

2. **Mutate `AnyToolchainState` Union in `ontology.py`**
   - Modify the `AnyToolchainState` type alias to include `NetworkInterceptState` and `MemoryHeapSnapshot`.

3. **Inject `SchemaInferenceIntent` in `ontology.py`**
   - Add new class inheriting from `CoreasonBaseState`.
   - Define fields, including `sampled_micro_batch` which needs a `@field_validator(..., mode="before")` that uses `_validate_payload_bounds(v)`.

4. **Mutate `AnyIntent` Union in `ontology.py`**
   - Modify the `AnyIntent` type alias to include `SchemaInferenceIntent`.

5. **Update `.model_rebuild()` Calls in `ontology.py`**
   - Append `.model_rebuild()` calls for `NetworkInterceptState`, `MemoryHeapSnapshot`, and `SchemaInferenceIntent` at the very end of the file.

6. **Update `__init__.py` Export Registry**
   - Add `"MemoryHeapSnapshot"`, `"NetworkInterceptState"`, and `"SchemaInferenceIntent"` to the `__all__` list in strictly alphabetical order.

7. **Verify Pre-Flight Constraints and Run Pre-Commit Checks**
   - Verify there are no execution side-effects.
   - Run `pre_commit_instructions` and follow them to format and check.
