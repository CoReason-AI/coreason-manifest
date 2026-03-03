1. **Remove Hardcoded Production Mocks**
   - File: `src/coreason_manifest/core/compute/epistemic.py`
   - Modify `ReifiedEntity` model. Delete `VALID_ONTOLOGY_MOCKS` and update the `@model_validator(mode="after")` on `ReifiedEntity` to check if a validation callable is injected via Pydantic `ValidationInfo.context`. If the callable is present, use it; otherwise, allow the ID to pass (or pass dynamically if configured).
   - *Verification*: Use `cat` or `read_file` to ensure `VALID_ONTOLOGY_MOCKS` is removed and validation is dynamic.

2. **Enforce Zero-Trust Cryptographic Signatures**
   - File: `src/coreason_manifest/ports/mcp.py`
   - Modify `append_clinical_proposition` to accept `agent_sig: AgentSignature` as an explicit required argument.
   - Remove the mock `AgentSignature` with `mock_hash`. Update the `context_envelope` to use the provided `agent_sig`.
   - *Verification*: Use `read_file` to ensure `append_clinical_proposition` signature is correct and mocks are removed.

3. **Stabilize Diffing Logic**
   - File: `src/coreason_manifest/core/workflow/flow_diff.py`
   - Inside `_get_id(item: Any)`, replace the non-deterministic `hash(str(item))` fallback with a deterministic JSON serialization `json.dumps(item, sort_keys=True)`.
   - *Verification*: Use `read_file` to verify the fallback logic uses deterministic state comparison.

4. **Fix Presentation-Layer Aliasing - visualizer**
   - File: `src/coreason_manifest/core/presentation/visualizer.py`
   - Remove the shim comment and the specific shim handling `"EmergenceInspectorNode"` names to display `"Emergence Inspector"`.
   - *Verification*: Use `read_file` to verify the shim is removed.

5. **Fix Presentation-Layer Aliasing - oversight**
   - File: `src/coreason_manifest/core/workflow/nodes/oversight.py`
   - Add a `@model_validator(mode='before')` to `EmergenceInspectorNode` that changes the `type` or legacy name from `"EmergenceInspectorNode"` to `"Emergence Inspector"`. Wait, the prompt says "normalize legacy node names upon *ingestion*, so the presentation layer only ever receives the clean, modern schema." Actually, I need to check how names are ingested, perhaps `name` field, or we just map it. The visualizer maps the `node.type` ("emergence_inspector"). Wait, visualizer says: `Legacy used "EmergenceInspectorNode", we stick to clean UI "Emergence Inspector"`. I will inspect `visualizer.py` again.
   - *Verification*: Use `read_file` to verify the ingestion normalization.

6. **Purge Dead-Code Exclusion Rules**
   - File: `pyproject.toml`
   - Remove `"if 0:"` from `[tool.coverage.report]` exclusions.
   - Run global grep for `if 0:` in `src/` and delete any dead code entirely.
   - *Verification*: Use `read_file` to ensure `pyproject.toml` no longer contains `"if 0:"` and `grep` shows no `if 0:` dead code.

7. **Remove Agile Jargon (Jira Leakage)**
   - File: `src/coreason_manifest/core/security/gatekeeper.py`
   - Replace Agile terms like "Epic 1 & 3 Binding", "Epic 5", "Epic 6" with permanent architectural references (e.g. `(Ref: ADR-014: Federated Search Guarding)` as asked in the prompt). The prompt says `For example, change (Epic 6) to (Ref: ADR-014: Federated Search Guarding)`.
   - *Verification*: Use `read_file` to ensure Agile jargon is gone.

8. **Neutralize Dramatic Terminology**
   - File: `src/coreason_manifest/core/security/gatekeeper.py`
   - Replace `"Defensive check for Draft Mode Fatality"` with `"Prevent null reference exception during draft mode traversal."`
   - Replace `"Ghost Guard Graph Injection Failure - Rewire edges"` with `"Handle non-linear edge rewiring for dynamic security guard insertion."`
   - *Verification*: Use `read_file` to ensure dramatic terminology is neutralized.

9. **Global "SOTA" Purge**
   - Files system-wide (e.g., `identity.py`, `reasoning.py`, `gatekeeper.py`, `stream.py`).
   - Scan for the acronym "SOTA" and replace it with objective technical descriptors (e.g., "Time-bounded validation").
   - *Verification*: Run `grep -ri sota src/` to verify no "SOTA" remains.

10. **Test Core Functionality**
    - Run `pytest` to ensure core functionality is not broken. Fix any tests failing due to the removal of mocks using `unittest.mock`.

11. **Complete pre commit steps**
    - Complete pre commit steps to ensure proper testing, verification, review, and reflection are done.

12. **Submit**
    - Submit the changes using the `submit` tool.
