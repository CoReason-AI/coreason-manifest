with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()

# Insert before AnyPresentationIntent (around line 6580 now)
insert_marker = "type AnyPresentationIntent = Annotated["

new_code = """class EpistemicZeroTrustContract(CoreasonBaseState):
    \"\"\"
    AGENT INSTRUCTION: The macroscopic task topology combining OpenSymbolicAI's data masking with SymbolicAI's logic enforcement.

    CAUSAL AFFORDANCE: Triggers the runtime to initiate a blind LLM inference cycle bounded by rigid mathematical proofs.

    EPISTEMIC BOUNDS: Bounded to a maximum of 10 remediation epochs to prevent thermodynamic free energy exhaustion. Arrays are deterministically sorted for RFC 8785 canonicalization.

    MCP ROUTING TRIGGERS: Bipartite Proposer-Verifier, Test-Time Compute, Zero-Trust Execution, Active Inference, Contract Topology
    \"\"\"
    topology_class: Literal["zero_trust_contract"] = Field(
        default="zero_trust_contract", description="Discriminator for a zero-trust contract."
    )
    intent_id: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")] = Field(
        description="UUIDv7 mapping to the ledger."
    )
    semantic_planning_task: Annotated[str, StringConstraints(max_length=4096)] = Field(
        description="The core semantic instruction for the blind LLM planner."
    )
    schema_blueprint_name: Annotated[str, StringConstraints(max_length=256)] = Field(
        description="The registered URI of the Pydantic schema used to generate the proxies."
    )
    structural_pre_conditions: list[EpistemicConstraintPolicy] = Field(
        default_factory=list,
        description="DbC bounds checked before inference."
    )
    structural_post_conditions: list[EpistemicConstraintPolicy] = Field(
        default_factory=list,
        description="DbC bounds checked after inference to ensure the structural plan is valid."
    )
    max_planning_remediation_epochs: int = Field(
        default=3,
        le=10,
        ge=0,
        description="Thermodynamic cap on SymbolicAI DbC retries."
    )

    @model_validator(mode="after")
    def _enforce_canonical_sort(self) -> Self:
        object.__setattr__(
            self, "structural_pre_conditions",
            sorted(self.structural_pre_conditions, key=operator.attrgetter("assertion_ast"))
        )
        object.__setattr__(
            self, "structural_post_conditions",
            sorted(self.structural_post_conditions, key=operator.attrgetter("assertion_ast"))
        )
        return self


"""

content = content.replace(insert_marker, new_code + insert_marker)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
