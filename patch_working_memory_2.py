with open("src/coreason_manifest/spec/ontology.py") as f:
    c = f.read()

c = c.replace(
    'affordance_projection: "OntologicalSurfaceProjection | None" = Field(',
    "affordance_projection: OntologicalSurfaceProjection | None = Field(",
)
c = c.replace(
    'capability_attestations: list["FederatedCapabilityAttestation"] = Field(',
    "capability_attestations: list[FederatedCapabilityAttestation] = Field(",
)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c)
