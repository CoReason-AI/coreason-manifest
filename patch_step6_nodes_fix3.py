with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()


old_semantic_edge_cid = """    confidence_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="The probabilistic certainty of this logical connection."
    )
    predicate: Annotated[str, StringConstraints(max_length=2000)] = Field(
        description="The string representation of the relationship (e.g., 'WORKS_FOR')."
    )"""

new_semantic_edge_cid = """    predicate_curie: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+:[a-zA-Z0-9_]+$")] = Field(json_schema_extra={"rdf_edge_property": True})
    belief_vector: DempsterShaferBeliefVector | None = Field(default=None)
    grounding_sla: EvidentiaryGroundingSLA | None = Field(default=None)"""

content = content.replace(old_semantic_edge_cid, new_semantic_edge_cid)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
