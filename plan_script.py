def generate_plan():
    print("""
1. **TARGET 1: Eradicate Base Classes**
   - Read the properties of `BaseStateEvent`, `BaseNodeProfile`, `BaseTopologyManifest`, and `BaseIntent`.
   - Iterate over all classes in `src/coreason_manifest/spec/ontology.py`.
   - For classes inheriting from `BaseStateEvent` (e.g. `SystemFaultEvent`, `ObservationEvent`, `TokenBurnReceipt`, etc.), replace inheritance with `CoreasonBaseState` and inline `event_id`, `prior_event_hash`, `timestamp`.
   - For classes inheriting from `BaseNodeProfile` (e.g. `AgentNodeProfile`, `HumanNodeProfile`, `SystemNodeProfile`, `CompositeNodeProfile`, `MemoizedNodeProfile`), replace inheritance with `CoreasonBaseState`, inline the 8 fields (`description`, `architectural_intent`, `justification`, `intervention_policies`, `domain_extensions`, `semantic_zoom`, `markov_blanket`, `optical_physics`), the `@field_validator("domain_extensions")`, and merge `_enforce_canonical_sort_intervention_policies` logic into the child classes' sorting validator.
   - For classes inheriting from `BaseTopologyManifest`, replace inheritance with `CoreasonBaseState` and inline the 8 fields (`epistemic_enforcement`, `lifecycle_phase`, `architectural_intent`, `justification`, `nodes`, `shared_state_contract`, `information_flow`, `observability`).
   - For `FYIIntent`, change base class from `BaseIntent` to `CoreasonBaseState`.
   - Remove definitions of `BaseStateEvent`, `BaseNodeProfile`, `BaseTopologyManifest`, and `BaseIntent`.

2. **TARGET 2: AST Bounding**
   - Refactor `NodeIdentifierState`, `ProfileIdentifierState`, `ToolIdentifierState`, and `TopologyHashReceipt` to move constraints (`min_length`, `max_length`, `pattern`) from `Field()` into `StringConstraints()`. E.g., `Annotated[str, StringConstraints(...), Field(description="...")]`.
   - Perform a global replacement of all `str = Field(...)` and `str | None = Field(...)` that have string constraints like `max_length` in them, rewriting them to `Annotated[str, StringConstraints(...)] = Field(...)` and `Annotated[str, StringConstraints(...)] | None = Field(...)`.

3. **TARGET 3: Merkle Array Sorting Loophole Closure**
   - Add a sorting `@model_validator` to `EpistemicChainGraphState` to physically sort its `syntactic_roots` array (`object.__setattr__(self, "syntactic_roots", sorted(self.syntactic_roots))`).
   - Confirm that sorting of `intervention_policies` in `BaseNodeProfile` children is correctly merged into any existing `_enforce_canonical_sort` (this is covered in Target 1).

4. **TARGET 4: Dead Code & Rebuild Cleanup**
   - Delete `BaseNodeProfile.model_rebuild()`, `BaseTopologyManifest.model_rebuild()`, and `BaseStateEvent.model_rebuild()` at the bottom of the file.
   - Verify no orphaned imports or conversational `# comments` left over from base class shattering.

5. **Pre Commit Checks**
   - Call `pre_commit_instructions` to ensure proper testing, verification, review, and reflection are done.

6. **Submit**
   - Submit the branch with the finalized architectural reset.
""")
generate_plan()
