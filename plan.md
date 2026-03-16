1. **Inject `SemanticGapAnalysisProfile` in `ontology.py`:**
   - Inherits from `CoreasonBaseState`.
   - Fields: `target_generation_id` (str with regex constraints), `hallucinated_claims` (list of constrained strings), `omitted_context` (list of constrained strings), `factual_overlap_ratio` (float [0.0, 1.0]).
   - Implement `@model_validator(mode="after")` to mathematically sort `hallucinated_claims` and `omitted_context`.

2. **Mutate `CognitiveCritiqueProfile` in `ontology.py`:**
   - Add field `flaw_taxonomy` with `Literal["hallucination", "omission", "contradiction", "sycophancy", "logical_leap"] | None`.

3. **Mutate `CognitiveDualVerificationReceipt` in `ontology.py`:**
   - Add field `adjudicator_escalation_id` of type `NodeIdentifierState | None`.

4. **Mutate `EpistemicAxiomVerificationReceipt` in `ontology.py`:**
   - Add field `tripped_falsification_condition_id` with type `str | None` and regex constraints.

5. **AST / Compilation Integrity in `ontology.py`:**
   - Add `SemanticGapAnalysisProfile.model_rebuild()` at the very end of the file.

6. **Module Export Registration in `__init__.py`:**
   - Add `"SemanticGapAnalysisProfile"` to the `__all__` list in `src/coreason_manifest/__init__.py` in strict alphabetical order.

7. **Pre-commit Steps:**
   - Ensure proper testing, verification, review, and reflection are done by calling the pre_commit_instructions tool.

8. **Submit:**
   - Call submit with descriptive title, commit message, description and branch name.
