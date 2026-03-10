with open("src/coreason_manifest/spec/ontology.py") as f:
    c = f.read()

target = """class FederatedDiscoveryProtocol(CoreasonBaseModel):
    \"\"\"
    A cross-boundary protocol for locating and authenticating external swarm clusters.
    \"\"\"

    protocol_version: str = Field(description="The semantic version of the FDP specification.")
    broadcast_endpoints: list[HttpUrl] = Field(
        min_length=1, description="The mathematical endpoints to broadcast discovery pings."
    )
    supported_ontologies: list[str] = Field(
        default_factory=list, description="The semantic URIs this cluster is capable of processing."
    )
    handshake_contract: OntologicalHandshake = Field(
        description="The mathematical proof required to initiate cluster peering."
    )"""

replacement = (
    target
    + """

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "broadcast_endpoints", sorted(self.broadcast_endpoints, key=str))
        object.__setattr__(self, "supported_ontologies", sorted(self.supported_ontologies))
        return self"""
)

c = c.replace(target, replacement)
with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c)
