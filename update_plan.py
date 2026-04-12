plan = """1. **Refactor `DocumentLayoutRegionState`**:
   - Update `block_class` field type to literal containing `"header", "paragraph", "figure", "table", "footnote", "caption", "equation", "list_item", "code_block", "form_field"`.

2. **Create `SchemaDrivenExtractionSLA`**:
   - Create class inheriting from `CoreasonBaseState`.
   - Add fields `schema_registry_uri` (`AnyUrl`), `extraction_framework` (`Literal["docling_graph_explicit", "ontogpt_spires"]`), `max_schema_retries` (`int` between 0 and 10), and `validation_failure_action` (`Literal["quarantine_chunk", "escalate_to_human", "drop_edge"]`).

3. **Create `EvidentiaryGroundingSLA`**:
   - Create class inheriting from `CoreasonBaseState`.
   - Add fields `minimum_nli_entailment_score` (`float` bounded by `ge=0.0, le=1.0`), `require_independent_sources` (`int` bounded by `ge=1, le=10`, default `1`), `ungrounded_link_action` (`Literal["sever_edge", "flag_for_human", "decay_weight"]`, default `"sever_edge"`), and `allowed_evidence_domains` (`list[Annotated[str, StringConstraints(max_length=255)]]`).
   - Add a `@model_validator(mode="after")` to deterministically sort the `allowed_evidence_domains` list.

4. **Refactor `EpistemicTransmutationTask`**:
   - Add `"semantic_graph"` to the `target_modalities` Literal array.
   - Replace generic compression fields (delete `compression_sla`) with `schema_governance: SchemaDrivenExtractionSLA | None = Field(default=None)`.
   - Add a `@model_validator(mode="after")` named `validate_graph_schema_presence` to raise a `ValueError` if `"semantic_graph"` is in `target_modalities` but `schema_governance` is `None`.

5. **Rename `DempsterShaferBeliefState`**:
   - Rename existing class `DempsterShaferBeliefState` to `DempsterShaferBeliefVector`.
   - Rename all references of `DempsterShaferBeliefState` to `DempsterShaferBeliefVector` across the file.

6. **Refactor Semantic Nodes and Edges (`SemanticNodeState`, `SemanticEdgeState`, `CausalDirectedEdgeState`)**:
   - In `SemanticNodeState`:
     - Update `node_cid` Field with `json_schema_extra={"rdf_subject": True}`.
     - Add `canonical_uri: AnyUrl | None = Field(default=None, json_schema_extra={"rdf_predicate": "owl:sameAs"})`.
     - Update `label` Field with `json_schema_extra={"rdf_predicate": "rdfs:label"}`.
     - Update `text_chunk` Field with `json_schema_extra={"rdf_predicate": "schema:description"}`.
   - In `SemanticEdgeState`:
     - Remove `confidence_score`.
     - Update `predicate` to `predicate_curie: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+:[a-zA-Z0-9_]+$")] = Field(json_schema_extra={"rdf_edge_property": True})`.
     - Add `belief_vector: DempsterShaferBeliefVector | None = Field(default=None)`.
     - Add `grounding_sla: EvidentiaryGroundingSLA | None = Field(default=None)`.
     - Add `@model_validator(mode="after")` named `enforce_evidence_or_sla` to raise a `ValueError` if BOTH `belief_vector` and `grounding_sla` are `None`.
   - In `CausalDirectedEdgeState`:
     - Remove `confidence_score` (if it existed) and apply the exact same additions (`predicate_curie`, `belief_vector`, `grounding_sla`, and validator) as `SemanticEdgeState`.

7. **Create Execution Intents and Receipts**:
   - `DocumentKnowledgeGraphManifest`:
     - inherits `CoreasonBaseState`
     - `graph_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]`
     - `source_artifact_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]`
     - `nodes: list[SemanticNodeState] = Field(max_length=100000)`
     - `causal_edges: list[CausalDirectedEdgeState] = Field(max_length=100000)`
     - `isomorphism_hash: Annotated[str, StringConstraints(pattern="^[a-f0-9]{64}$")]`
     - `@model_validator` to sort `nodes` by `node_cid` and `causal_edges` by `source_variable`/`target_variable`.
   - `CausalPropagationIntent`:
     - inherits `CoreasonBaseState`
     - `topology_class: Literal["causal_propagation"] = "causal_propagation"`
     - `target_graph_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]`
     - `unverified_edges: list[CausalDirectedEdgeState]`
     - `@model_validator` to sort `unverified_edges` by `source_variable`/`target_variable`.
   - `BeliefModulationReceipt`:
     - inherits `CoreasonBaseState`
     - `topology_class: Literal["belief_modulation"] = "belief_modulation"`
     - `receipt_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]`
     - `target_graph_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]`
     - `grounded_edges: dict[Annotated[str, StringConstraints(max_length=255)], DempsterShaferBeliefVector]`
     - `severed_edge_cids: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]]`
     - `@model_validator` to sort `severed_edge_cids`.
   - `RDFSerializationIntent`:
     - inherits `CoreasonBaseState`
     - `topology_class: Literal["rdf_serialization"] = "rdf_serialization"`
     - `export_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]`
     - `target_graph_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]`
     - `target_format: Literal["turtle", "xml", "json-ld", "ntriples"] = "turtle"`
     - `base_uri_namespace: AnyUrl`
   - `RDFExportReceipt`:
     - inherits `CoreasonBaseState`
     - `topology_class: Literal["rdf_export_receipt"] = "rdf_export_receipt"`
     - `export_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]`
     - `serialized_payload: str`
     - `sha256_graph_hash: Annotated[str, StringConstraints(pattern="^[a-f0-9]{64}$")]`

8. **Update TypeAlias Unions and Rebuilds**:
   - Add `CausalPropagationIntent` and `RDFSerializationIntent` to `AnyIntent`.
   - Add `BeliefModulationReceipt` and `RDFExportReceipt` to `AnyStateEvent`.
   - Add `DocumentKnowledgeGraphManifest` to `AnyTopologyManifest`.
   - Add `.model_rebuild()` for the new classes at the end of the file.

9. **Bridge `algebra.py`**:
   - Update logic in `src/coreason_manifest/utils/algebra.py` to extract weights from the new `DempsterShaferBeliefVector`. Wherever `edge.confidence_score` is referenced, change the logic to check `if edge.belief_vector: weight = edge.belief_vector.semantic_distance` (or similar). If `belief_vector` is `None`, default to `0.0`.

10. **Update Fleet Taxonomy in `AGENTS.md`**:
    - Append the exact requested markdown content detailing SOTA 2026+ Open-Source Substrate Oracles.

11. **Format and lint**:
    - Run `uv run ruff format .` and `uv run ruff check . --fix`.

12. **Type check**:
    - Run `uv run mypy src/ tests/`.

13. **Run tests**:
    - Run `uv run pytest tests/`. If tests fail due to the breaking changes, use `read_file` to investigate the failing test files and edit them to provide the newly required `belief_vector` or `grounding_sla`.

14. **Complete pre-commit steps**:
    - Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.

15. **Submit**:
    - Submit changes.
"""
print(plan)
