with open("src/coreason_manifest/spec/ontology.py") as f:
    print("affordance_projection: OntologicalSurfaceProjection | None = Field(" in f.read())

with open("src/coreason_manifest/spec/ontology.py") as f:
    print("capability_attestations: list[FederatedCapabilityAttestation] = Field(" in f.read())
