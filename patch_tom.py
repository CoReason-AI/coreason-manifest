with open("src/coreason_manifest/spec/ontology.py") as f:
    c = f.read()

# Let's do string replacement instead for safety

target = """class TheoryOfMindSnapshot(CoreasonBaseModel):
    target_agent_id: str = Field(
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this node to the agent whose mind is being modeled.",  # noqa: E501
    )
    assumed_shared_beliefs: list[str] = Field(
        description="A list of Content Identifiers (CIDs) acting as cryptographic Lineage Watermarks that the modeling agent assumes the target already possesses."  # noqa: E501
    )
    identified_knowledge_gaps: list[str] = Field(
        description="Specific topics or logical premises the target agent is assumed to be missing."
    )"""

replacement = (
    target
    + """

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "assumed_shared_beliefs", sorted(self.assumed_shared_beliefs))
        object.__setattr__(self, "identified_knowledge_gaps", sorted(self.identified_knowledge_gaps))
        return self"""
)

c = c.replace(target, replacement)
with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c)
