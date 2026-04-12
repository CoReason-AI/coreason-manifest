1. **Refactor `DocumentLayoutRegionState`**:
   - Update `block_class` field type to literal containing `"header", "paragraph", "figure", "table", "footnote", "caption", "equation", "list_item", "code_block", "form_field"`.

2. **Create `SchemaDrivenExtractionSLA`**:
   - Create class inheriting from `CoreasonBaseState`.
   - Add fields `schema_registry_uri` (`AnyUrl`), `extraction_framework` (`Literal["docling_graph_explicit", "ontogpt_spires"]`), `max_schema_retries` (`int` between 0 and 10), and `validation_failure_action` (`Literal["quarantine_chunk", "escalate_to_human", "drop_edge"]`).

3. **Create `EvidentiaryGroundingSLA`**:
   - Create class inheriting from `CoreasonBaseState`.
   - Add fields `minimum_nli_entailment_score` (`float` bounded by `ge=0.0, le=1.0`), `require_independent_sources` (`int` bounded by `ge=1, le=10`, default `1`), `ungrounded_link_action` (`Literal["sever_edge", "flag_for_human", "decay_weight"]`, default `"sever_edge"`), and `allowed_evidence_domains` (`list[Annotated[str, StringConstraints(max_length=255)]]`).
   - Add a `@model_validator(mode="after")` named `_enforce_canonical_sort` to deterministically sort the `allowed_evidence_domains` list.

4. **Refactor `EpistemicTransmutationTask`**:
   - Add `"semantic_graph"` to the `target_modalities` Literal array.
   - Replace generic compression fields (delete `compression_sla`) with `schema_governance: SchemaDrivenExtractionSLA | None = Field(default=None)`.
   - Add a `@model_validator(mode="after")` named `validate_graph_schema_presence` to raise a `ValueError` if `"semantic_graph"` is in `target_modalities` but `schema_governance` is `None`.

5. **Refactor Semantic Nodes and Edges (`SemanticNodeState`, `SemanticEdgeState`, `CausalDirectedEdgeState`)**:
   - In `SemanticNodeState`:
     - Update `node_cid` Field with `json_schema_extra={"rdf_subject": True}`.
     - Add `canonical_uri: AnyUrl | None = Field(default=None, json_schema_extra={"rdf_predicate": "owl:sameAs"})`.
     - Update `label` Field with `json_schema_extra={"rdf_predicate": "rdfs:label"}`.
     - Update `text_chunk` Field with `json_schema_extra={"rdf_predicate": "schema:description"}`.
   - In `SemanticEdgeState`:
     - Remove `confidence_score`.
     - Update `predicate` to `predicate_curie: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+:[a-zA-Z0-9_]+$")] = Field(json_schema_extra={"rdf_edge_property": True})`.
     - Add `belief_vector: DempsterShaferBeliefState | None = Field(default=None)`.
     - Add `grounding_sla: EvidentiaryGroundingSLA | None = Field(default=None)`.
     - Add `@model_validator(mode="after")` named `enforce_evidence_or_sla` to raise a `ValueError` if BOTH `belief_vector` and `grounding_sla` are `None`.
   - In `CausalDirectedEdgeState`:
     - Note: `CausalDirectedEdgeState` doesn't seem to have `confidence_score` or `predicate` by default but it will be updated as requested. It needs `predicate_curie`? Wait, the instructions say:
     "Target: `SemanticEdgeState` & `CausalDirectedEdgeState`"
     "- Delete: `confidence_score` (and any related float probabilities on edges)."
     "- Add/Update: `predicate_curie: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+:[a-zA-Z0-9_]+$")] = Field(json_schema_extra={"rdf_edge_property": True})`."
     "- Add: `belief_vector: DempsterShaferBeliefState | None = Field(default=None)`."
     "- Add: `grounding_sla: EvidentiaryGroundingSLA | None = Field(default=None)`."
     "- Validator: Add `@model_validator(mode="after")` named `enforce_evidence_or_sla` to raise a `ValueError` if BOTH `belief_vector` and `grounding_sla` are `None`."
     I'll apply these to both `SemanticEdgeState` and `CausalDirectedEdgeState`. Wait, `DempsterShaferBeliefVector` in the prompt is probably `DempsterShaferBeliefState` in code, since I saw `DempsterShaferBeliefState` in the file. Wait, in prompt: `DempsterShaferBeliefVector`. In file: `DempsterShaferBeliefState`. I will use `DempsterShaferBeliefState`.

6. **Create Execution Intents and Receipts**:
   - `DocumentKnowledgeGraphManifest`:
     - inherits `CoreasonBaseState`
     - `topology_class: Literal["document_knowledge_graph"] = "document_knowledge_graph"`
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
     - `task_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]` (from step 3.2 in plan)
     - `grounding_sla: EvidentiaryGroundingSLA`
     - `unverified_edges: list[CausalDirectedEdgeState]`
     - `@model_validator` to sort `unverified_edges` by `source_variable`/`target_variable`.
   - `BeliefModulationReceipt`:
     - inherits `CoreasonBaseState`
     - `topology_class: Literal["belief_modulation"] = "belief_modulation"`
     - `receipt_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]`
     - `target_graph_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]`
     - `grounded_edges: dict[Annotated[str, StringConstraints(max_length=255)], DempsterShaferBeliefState]`
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
     - `rdf_triple_count: int`
     - `sha256_graph_hash: Annotated[str, StringConstraints(pattern="^[a-f0-9]{64}$")]`

7. **Update TypeAlias Unions and Rebuilds**:
   - Add `CausalPropagationIntent` and `RDFSerializationIntent` to `AnyIntent`.
   - Add `BeliefModulationReceipt` and `RDFExportReceipt` to `AnyStateEvent`.
   - Add `DocumentKnowledgeGraphManifest` to `AnyTopologyManifest`.
   - Add `.model_rebuild()` for the new classes at the end of the file.

8. **Update Fleet Taxonomy in `AGENTS.md`**:
   - Append the exact requested markdown content detailing SOTA 2026+ Open-Source Substrate Oracles.

9. **Code verification and pre-commit**:
   - Run `uv run ruff format .` and `uv run ruff check . --fix`.
   - Run `uv run mypy src/ tests/`.
   - Run tests and fix any failing tests due to breaking changes.
   - Run `pre_commit_instructions` tool to perform pre-commit checks.

10. **Submit**:
    - Submit changes.
