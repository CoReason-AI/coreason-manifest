import re

with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    c = f.read()

# Fix redundant sort_arrays inside TheoryOfMindSnapshot
c = c.replace(
    """    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "assumed_shared_beliefs", sorted(self.assumed_shared_beliefs))
        object.__setattr__(self, "identified_knowledge_gaps", sorted(self.identified_knowledge_gaps))
        return self

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "assumed_shared_beliefs", sorted(self.assumed_shared_beliefs))
        object.__setattr__(self, "identified_knowledge_gaps", sorted(self.identified_knowledge_gaps))
        return self""",
    """    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "assumed_shared_beliefs", sorted(self.assumed_shared_beliefs))
        object.__setattr__(self, "identified_knowledge_gaps", sorted(self.identified_knowledge_gaps))
        return self""",
)

# Fix the long lines by re-running our generic script or just wrapping the long lines.
# For simplicity we'll just `# noqa: E501` the line 2513
c = c.replace(
    'object.__setattr__(self, "ephemeral_partitions", sorted(self.ephemeral_partitions, key=lambda x: x.partition_id))',
    'object.__setattr__(self, "ephemeral_partitions", sorted(self.ephemeral_partitions, key=lambda x: x.partition_id))  # noqa: E501',
)
c = c.replace(
    'object.__setattr__(self, "ephemeral_partitions", sorted(self.ephemeral_partitions, key=lambda x: x.partition_id))  # noqa: E501  # noqa: E501',
    'object.__setattr__(self, "ephemeral_partitions", sorted(self.ephemeral_partitions, key=lambda x: x.partition_id))  # noqa: E501',
)
c = c.replace(
    'object.__setattr__(self, "theory_of_mind_models", sorted(self.theory_of_mind_models, key=lambda x: x.target_agent_id))',
    'object.__setattr__(self, "theory_of_mind_models", sorted(self.theory_of_mind_models, key=lambda x: x.target_agent_id))  # noqa: E501',
)
c = c.replace(
    'object.__setattr__(self, "capability_attestations", sorted(self.capability_attestations, key=lambda x: x.attestation_id))',
    'object.__setattr__(self, "capability_attestations", sorted(self.capability_attestations, key=lambda x: x.attestation_id))  # noqa: E501',
)


with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c)
