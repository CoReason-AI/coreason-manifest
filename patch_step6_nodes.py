with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()


# SemanticNodeState
old_node_cid = """    node_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")] = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this semantic node to the Merkle-DAG.",
    )"""
new_node_cid = """    node_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")] = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this semantic node to the Merkle-DAG.",
        json_schema_extra={"rdf_subject": True}
    )
    canonical_uri: AnyUrl | None = Field(default=None, json_schema_extra={"rdf_predicate": "owl:sameAs"})"""
content = content.replace(old_node_cid, new_node_cid)

old_label = """    label: Annotated[str, StringConstraints(max_length=2000)] = Field(
        description="The categorical label of the node (e.g., 'Person', 'Concept')."
    )"""
new_label = """    label: Annotated[str, StringConstraints(max_length=2000)] = Field(
        description="The categorical label of the node (e.g., 'Person', 'Concept').",
        json_schema_extra={"rdf_predicate": "rdfs:label"}
    )"""
content = content.replace(old_label, new_label)

old_text_chunk = """    text_chunk: Annotated[str, StringConstraints(max_length=50000)] = Field(
        description="The raw natural language representation of the semantic node."
    )"""
new_text_chunk = """    text_chunk: Annotated[str, StringConstraints(max_length=50000)] = Field(
        description="The raw natural language representation of the semantic node.",
        json_schema_extra={"rdf_predicate": "schema:description"}
    )"""
content = content.replace(old_text_chunk, new_text_chunk)


# SemanticEdgeState
old_semantic_edge_cid = """    confidence_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="The probabilistic certainty of this logical connection."
    )
    predicate: Annotated[str, StringConstraints(max_length=2000)] = Field(
        description="The formal ontological connection between the subject and object."
    )"""

new_semantic_edge_cid = """    predicate_curie: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+:[a-zA-Z0-9_]+$")] = Field(json_schema_extra={"rdf_edge_property": True})
    belief_vector: DempsterShaferBeliefVector | None = Field(default=None)
    grounding_sla: EvidentiaryGroundingSLA | None = Field(default=None)"""

content = content.replace(old_semantic_edge_cid, new_semantic_edge_cid)

# Add validator to SemanticEdgeState
validator_code = """
    @model_validator(mode="after")
    def enforce_evidence_or_sla(self) -> Self:
        if self.belief_vector is None and self.grounding_sla is None:
            raise ValueError("Edge must possess either empirical evidence (belief_vector) or an explicit grounding_sla.")
        return self
"""
content = content.replace(
    "class SemanticEdgeState(CoreasonBaseState):", "class SemanticEdgeState(CoreasonBaseState):" + validator_code
)

# CausalDirectedEdgeState
old_causal_edge = """    edge_class: Literal["direct_cause", "confounder", "collider", "mediator"] = Field(
        description="The specific Pearlian topological relationship between the two variables."
    )
"""
new_causal_edge = """    edge_class: Literal["direct_cause", "confounder", "collider", "mediator"] = Field(
        description="The specific Pearlian topological relationship between the two variables."
    )
    predicate_curie: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+:[a-zA-Z0-9_]+$")] = Field(json_schema_extra={"rdf_edge_property": True})
    belief_vector: DempsterShaferBeliefVector | None = Field(default=None)
    grounding_sla: EvidentiaryGroundingSLA | None = Field(default=None)

    @model_validator(mode="after")
    def enforce_evidence_or_sla(self) -> Self:
        if self.belief_vector is None and self.grounding_sla is None:
            raise ValueError("Causal edge must possess either empirical evidence (belief_vector) or an explicit grounding_sla.")
        return self
"""
content = content.replace(old_causal_edge, new_causal_edge)

# CausalDirectedEdgeState did not have a confidence_score but if it did somewhere else, we would remove it, let's check
if "confidence_score" in content and "class CausalDirectedEdgeState" in content:
    pass  # we'll see if it fails

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
