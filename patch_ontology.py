import re

with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

# Step 1: Inject SemanticGapAnalysisProfile before CognitiveCritiqueProfile
new_class = """class SemanticGapAnalysisProfile(CoreasonBaseState):
    \"\"\"
    AGENT INSTRUCTION: A rigid set-theoretic evaluation matrix comparing generated claims against factual grounding. Isolates hallucinations and omissions.
    \"\"\"

    target_generation_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The CID of the LLM generation being evaluated.",
    )
    hallucinated_claims: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        default_factory=list,
        description="Represents G \\\\ F: Claims generated but not present in the source facts.",
    )
    omitted_context: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        default_factory=list,
        description="Represents F \\\\ G: Critical facts present in the source but missing from the generation.",
    )
    factual_overlap_ratio: float = Field(
        ge=0.0,
        le=1.0,
        description="The Jaccard index or structural overlap between the two sets.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "hallucinated_claims", sorted(self.hallucinated_claims))
        object.__setattr__(self, "omitted_context", sorted(self.omitted_context))
        return self


"""

content = content.replace("class CognitiveCritiqueProfile(CoreasonBaseState):", new_class + "class CognitiveCritiqueProfile(CoreasonBaseState):")

# Step 2: Mutate CognitiveCritiqueProfile
old_ccp_field = """    epistemic_penalty_scalar: float = Field(
        ge=0.0,
        le=1.0,
        description="CoReason Shared Kernel Ontology: A continuous penalty applied to the branch's probability mass if normative drift or hallucination is detected.",  # noqa: E501
    )"""
new_ccp_field = """    epistemic_penalty_scalar: float = Field(
        ge=0.0,
        le=1.0,
        description="CoReason Shared Kernel Ontology: A continuous penalty applied to the branch's probability mass if normative drift or hallucination is detected.",  # noqa: E501
    )
    flaw_taxonomy: Literal["hallucination", "omission", "contradiction", "sycophancy", "logical_leap"] | None = Field(
        default=None,
        description="The strict categorical classification of the reasoning flaw, allowing the orchestrator to route to specific deterministic remediation templates.",
    )"""

content = content.replace(old_ccp_field, new_ccp_field)


# Step 3: Mutate CognitiveDualVerificationReceipt
old_cdvr = """    trace_factual_alignment: bool = Field(
        description="Strict Boolean indicating if BOTH agents mathematically agree on factual alignment."
    )"""
new_cdvr = """    trace_factual_alignment: bool = Field(
        description="Strict Boolean indicating if BOTH agents mathematically agree on factual alignment."
    )
    adjudicator_escalation_id: NodeIdentifierState | None = Field(
        default=None,
        description="The deterministic tie-breaker node (e.g., a more powerful model or human oversight) invoked if the primary and secondary verifiers disagree.",
    )"""

content = content.replace(old_cdvr, new_cdvr)

# Step 4: Mutate EpistemicAxiomVerificationReceipt
old_eavr = """    fact_score_passed: bool"""
new_eavr = """    fact_score_passed: bool
    tripped_falsification_condition_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The specific condition_id from a FalsificationContract that this axiom mathematically violated.",
    )"""

content = content.replace(old_eavr, new_eavr)

# Step 5: AST / Compilation Integrity in ontology.py
old_rebuilds = """WorkflowManifest.model_rebuild()
ProgramSynthesisIntent.model_rebuild()
SymbolicExecutionReceipt.model_rebuild()"""
new_rebuilds = """WorkflowManifest.model_rebuild()
ProgramSynthesisIntent.model_rebuild()
SymbolicExecutionReceipt.model_rebuild()
SemanticGapAnalysisProfile.model_rebuild()"""

content = content.replace(old_rebuilds, new_rebuilds)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)

print("Patch applied.")
