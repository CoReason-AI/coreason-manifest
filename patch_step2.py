with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()

# Insert SchemaDrivenExtractionSLA and EvidentiaryGroundingSLA just above EpistemicTransmutationTask (or near it)
insert_marker = "class EpistemicTransmutationTask(CoreasonBaseState):"
new_classes = """class SchemaDrivenExtractionSLA(CoreasonBaseState):
    schema_registry_uri: AnyUrl = Field(description="RFC 8785 canonicalized URI to the exact Pydantic template or LinkML definition.")
    extraction_framework: Literal["docling_graph_explicit", "ontogpt_spires"] = Field(...)
    max_schema_retries: int = Field(ge=0, le=10)
    validation_failure_action: Literal["quarantine_chunk", "escalate_to_human", "drop_edge"]

class EvidentiaryGroundingSLA(CoreasonBaseState):
    minimum_nli_entailment_score: float = Field(ge=0.0, le=1.0)
    require_independent_sources: int = Field(ge=1, le=10, default=1)
    ungrounded_link_action: Literal["sever_edge", "flag_for_human", "decay_weight"] = Field(default="sever_edge")
    allowed_evidence_domains: list[Annotated[str, StringConstraints(max_length=255)]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _enforce_canonical_sort(self) -> Self:
        object.__setattr__(self, "allowed_evidence_domains", sorted(self.allowed_evidence_domains))
        return self

"""

content = content.replace(insert_marker, new_classes + insert_marker)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
