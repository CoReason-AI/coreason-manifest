with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()


# We will append the new classes right before the type alias definitions.
# Look for "type AnyIntent =" and insert before it.

insert_marker = "type AnyIntent = Annotated["

new_classes = """class DocumentKnowledgeGraphManifest(CoreasonBaseState):
    graph_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]
    source_artifact_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]
    nodes: list[SemanticNodeState] = Field(max_length=100000)
    causal_edges: list[CausalDirectedEdgeState] = Field(max_length=100000)
    isomorphism_hash: Annotated[str, StringConstraints(pattern="^[a-f0-9]{64}$")]

    @model_validator(mode="after")
    def _enforce_canonical_sort(self) -> Self:
        object.__setattr__(self, "nodes", sorted(self.nodes, key=operator.attrgetter("node_cid")))
        object.__setattr__(self, "causal_edges", sorted(self.causal_edges, key=lambda e: (e.source_variable, e.target_variable)))
        return self

class CausalPropagationIntent(CoreasonBaseState):
    topology_class: Literal["causal_propagation"] = "causal_propagation"
    target_graph_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]
    unverified_edges: list[CausalDirectedEdgeState]

    @model_validator(mode="after")
    def _enforce_canonical_sort(self) -> Self:
        object.__setattr__(self, "unverified_edges", sorted(self.unverified_edges, key=lambda e: (e.source_variable, e.target_variable)))
        return self

class BeliefModulationReceipt(CoreasonBaseState):
    topology_class: Literal["belief_modulation"] = "belief_modulation"
    receipt_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]
    target_graph_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]
    grounded_edges: dict[Annotated[str, StringConstraints(max_length=255)], DempsterShaferBeliefVector]
    severed_edge_cids: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]]

    @model_validator(mode="after")
    def _enforce_canonical_sort(self) -> Self:
        object.__setattr__(self, "severed_edge_cids", sorted(self.severed_edge_cids))
        return self

class RDFSerializationIntent(CoreasonBaseState):
    topology_class: Literal["rdf_serialization"] = "rdf_serialization"
    export_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]
    target_graph_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]
    target_format: Literal["turtle", "xml", "json-ld", "ntriples"] = "turtle"
    base_uri_namespace: AnyUrl

class RDFExportReceipt(CoreasonBaseState):
    topology_class: Literal["rdf_export_receipt"] = "rdf_export_receipt"
    export_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]
    serialized_payload: str
    sha256_graph_hash: Annotated[str, StringConstraints(pattern="^[a-f0-9]{64}$")]

"""

content = content.replace(insert_marker, new_classes + insert_marker)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
