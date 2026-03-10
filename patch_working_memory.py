with open("src/coreason_manifest/spec/ontology.py") as f:
    c = f.read()

target = """class WorkingMemorySnapshot(CoreasonBaseModel):
    \"\"\"
    A temporally isolated epistemic scratchpad.
    Strictly forbids access to the Global Epistemic Ledger without explicit projection.
    \"\"\"

    session_id: str = Field(description="The ephemeral session boundary for this execution.")
    affordance_projection: "OntologicalSurfaceProjection | None" = Field(
        default=None,
        description="The strictly bounded subset of Tools and APIs legally authorized for this working memory block.",
    )
    active_context: dict[str, str] = Field(
        description="The ephemeral latent variables and environmental bindings currently active in Epistemic Quarantine."  # noqa: E501
    )
    argumentation: ArgumentGraph | None = Field(
        default=None,
        description="The localized, non-monotonic graph of defeasible attacks currently active in the swarm's working memory.",  # noqa: E501
    )
    theory_of_mind_models: list[TheoryOfMindSnapshot] = Field(
        default_factory=list, description="Epistemic models of other agents to align interaction manifolds."
    )
    capability_attestations: list["FederatedCapabilityAttestation"] = Field(
        default_factory=list,
        description="Zero-Knowledge Proofs or hardware signatures granting elevated zero-trust capabilities to this exact context window.",  # noqa: E501
    )"""

replacement = """class WorkingMemorySnapshot(CoreasonBaseModel):
    \"\"\"
    A temporally isolated epistemic scratchpad.
    Strictly forbids access to the Global Epistemic Ledger without explicit projection.
    \"\"\"

    session_id: str = Field(description="The ephemeral session boundary for this execution.")
    affordance_projection: OntologicalSurfaceProjection | None = Field(
        default=None,
        description="The strictly bounded subset of Tools and APIs legally authorized for this working memory block.",
    )
    active_context: dict[str, str] = Field(
        description="The ephemeral latent variables and environmental bindings currently active in Epistemic Quarantine."  # noqa: E501
    )
    argumentation: ArgumentGraph | None = Field(
        default=None,
        description="The localized, non-monotonic graph of defeasible attacks currently active in the swarm's working memory.",  # noqa: E501
    )
    theory_of_mind_models: list[TheoryOfMindSnapshot] = Field(
        default_factory=list, description="Epistemic models of other agents to align interaction manifolds."
    )
    capability_attestations: list[FederatedCapabilityAttestation] = Field(
        default_factory=list,
        description="Zero-Knowledge Proofs or hardware signatures granting elevated zero-trust capabilities to this exact context window.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "theory_of_mind_models", sorted(self.theory_of_mind_models, key=lambda x: x.target_agent_id))
        object.__setattr__(self, "capability_attestations", sorted(self.capability_attestations, key=lambda x: x.attestation_id))
        return self"""

c = c.replace(target, replacement)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c)
