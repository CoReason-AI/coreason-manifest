with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

# TaxonomicRoutingPolicy modifications
import re

taxonomic_old = """class TaxonomicRoutingPolicy(CoreasonBaseState):
    \"\"\"
    The deterministic Softmax gate mapping classified operational intents to pre-defined
    spatial organizing frameworks to prevent token exhaustion.
    \"\"\"

    policy_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this pre-flight routing policy.",
    )
    intent_to_heuristic_matrix: dict[
        Annotated[str, StringConstraints(max_length=255)],
        Literal["chronological", "entity_centric", "semantic_cluster", "confidence_decay"],
    ] = Field(
        max_length=1000,
        description="Strict dictionary binding classified natural language intents to bounded spatial heuristics.",
    )"""

taxonomic_new = """class TaxonomicRoutingPolicy(CoreasonBaseState):
    \"\"\"
    The deterministic Softmax gate mapping classified operational intents to pre-defined
    spatial organizing frameworks to prevent token exhaustion.
    \"\"\"

    policy_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this pre-flight routing policy.",
    )
    intent_to_heuristic_matrix: dict[
        ValidRoutingIntent,
        Literal["chronological", "entity_centric", "semantic_cluster", "confidence_decay"],
    ] = Field(
        max_length=1000,
        description="Strict dictionary binding classified natural language intents to bounded spatial heuristics.",
    )
    superposition_branching_threshold: float = Field(default=0.85)

    @model_validator(mode="after")
    def validate_domain_extensions(self, info: ValidationInfo) -> Self:
        allowed_exts = (info.context or {}).get("allowed_ext_intents", set())
        for k, v in self.__dict__.items():
            if isinstance(v, str) and v.startswith("ext:") and v not in allowed_exts:
                raise ValueError(f"Unauthorized extension string in field {k}: {v}")
            elif isinstance(v, dict):
                for dk, dv in v.items():
                    if isinstance(dk, str) and dk.startswith("ext:") and dk not in allowed_exts:
                        raise ValueError(f"Unauthorized extension string in dict key of {k}: {dk}")
                    if isinstance(dv, str) and dv.startswith("ext:") and dv not in allowed_exts:
                        raise ValueError(f"Unauthorized extension string in dict value of {k}: {dv}")
        return self"""

if taxonomic_old in content:
    content = content.replace(taxonomic_old, taxonomic_new)
    print("Patched TaxonomicRoutingPolicy")
else:
    print("TaxonomicRoutingPolicy not found!")

# DifferentiableLogicConstraint modifications
diff_logic_old = """class DifferentiableLogicConstraint(CoreasonBaseState):
    constraint_id: str = Field(max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", min_length=1)
    formal_syntax_smt: str = Field(
        max_length=2000, description="The formal SMT-LIB or Lean4 language representation of the symbolic rule."
    )
    relaxation_epsilon: float = Field(
        le=1.0,
        ge=0.0,
        description="The continuous penalty applied to the LLM probability mass for constraint violation.",
    )"""

diff_logic_new = """class DifferentiableLogicConstraint(CoreasonBaseState):
    constraint_id: str = Field(max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", min_length=1)
    formal_syntax_smt: str = Field(
        max_length=2000, description="The formal SMT-LIB or Lean4 language representation of the symbolic rule."
    )
    relaxation_epsilon: float = Field(
        le=1.0,
        ge=0.0,
        description="The continuous penalty applied to the LLM probability mass for constraint violation.",
    )
    anomaly_classification: IEEEAnomalyClass
    solver_status: SMTSolverOutcome = Field(default="unknown")

    @model_validator(mode="after")
    def validate_domain_extensions(self, info: ValidationInfo) -> Self:
        allowed_exts = (info.context or {}).get("allowed_ext_intents", set())
        for k, v in self.__dict__.items():
            if isinstance(v, str) and v.startswith("ext:") and v not in allowed_exts:
                raise ValueError(f"Unauthorized extension string in field {k}: {v}")
            elif isinstance(v, dict):
                for dk, dv in v.items():
                    if isinstance(dk, str) and dk.startswith("ext:") and dk not in allowed_exts:
                        raise ValueError(f"Unauthorized extension string in dict key of {k}: {dk}")
                    if isinstance(dv, str) and dv.startswith("ext:") and dv not in allowed_exts:
                        raise ValueError(f"Unauthorized extension string in dict value of {k}: {dv}")
        return self"""

if diff_logic_old in content:
    content = content.replace(diff_logic_old, diff_logic_new)
    print("Patched DifferentiableLogicConstraint")
else:
    print("DifferentiableLogicConstraint not found!")


# BargeInInterruptEvent modifications
barge_in_old = """class BargeInInterruptEvent(BaseStateEvent):
    \"\"\"A cryptographic receipt of a continuous multimodal sequence being prematurely severed by an external stimulus.\"\"\"

    type: Literal["barge_in"] = Field(
        default="barge_in", description="Discriminator type for a barge-in interruption event."
    )
    target_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the active node generation cycle that was killed in the Merkle-DAG.",  # noqa: E501
    )
    sensory_trigger: EmbodiedSensoryVectorProfile | None = Field(
        default=None,
        description="The continuous multimodal trigger (e.g., audio spike, user saying 'stop') that justified the interruption.",  # noqa: E501
    )
    retained_partial_payload: dict[Annotated[str, StringConstraints(max_length=255)], Any] | str | None = Field(
        max_length=100000,
        default=None,
        description="The 'stutter' state: the incomplete fragment of thought or text appended before the kill signal.",
    )
    epistemic_disposition: Literal["discard", "retain_as_context", "mark_as_falsified"] = Field(
        description="Explicit instruction to the orchestrator on how to patch the shared state blackboard with the partial payload."  # noqa: E501
    )"""

barge_in_new = """class BargeInInterruptEvent(BaseStateEvent):
    \"\"\"A cryptographic receipt of a continuous multimodal sequence being prematurely severed by an external stimulus.\"\"\"

    type: Literal["barge_in"] = Field(
        default="barge_in", description="Discriminator type for a barge-in interruption event."
    )
    target_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the active node generation cycle that was killed in the Merkle-DAG.",  # noqa: E501
    )
    sensory_trigger: EmbodiedSensoryVectorProfile | None = Field(
        default=None,
        description="The continuous multimodal trigger (e.g., audio spike, user saying 'stop') that justified the interruption.",  # noqa: E501
    )
    retained_partial_payload: dict[Annotated[str, StringConstraints(max_length=255)], Any] | str | None = Field(
        max_length=100000,
        default=None,
        description="The 'stutter' state: the incomplete fragment of thought or text appended before the kill signal.",
    )
    epistemic_disposition: Literal["discard", "retain_as_context", "mark_as_falsified"] = Field(
        description="Explicit instruction to the orchestrator on how to patch the shared state blackboard with the partial payload."  # noqa: E501
    )
    disfluency_type: DisfluencyRole
    evicted_token_count: int = Field(default=0)

    @model_validator(mode="after")
    def validate_domain_extensions(self, info: ValidationInfo) -> Self:
        allowed_exts = (info.context or {}).get("allowed_ext_intents", set())
        for k, v in self.__dict__.items():
            if isinstance(v, str) and v.startswith("ext:") and v not in allowed_exts:
                raise ValueError(f"Unauthorized extension string in field {k}: {v}")
            elif isinstance(v, dict):
                for dk, dv in v.items():
                    if isinstance(dk, str) and dk.startswith("ext:") and dk not in allowed_exts:
                        raise ValueError(f"Unauthorized extension string in dict key of {k}: {dk}")
                    if isinstance(dv, str) and dv.startswith("ext:") and dv not in allowed_exts:
                        raise ValueError(f"Unauthorized extension string in dict value of {k}: {dv}")
        return self"""

if barge_in_old in content:
    content = content.replace(barge_in_old, barge_in_new)
    print("Patched BargeInInterruptEvent")
else:
    print("BargeInInterruptEvent not found!")

# EpistemicAxiomState modifications
axiom_old = """class EpistemicAxiomState(CoreasonBaseState):
    source_concept_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="CID of the origin node."
    )
    directed_edge_type: str = Field(max_length=2000, description="The topological relationship.")
    target_concept_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="CID of destination node."
    )"""

axiom_new = """class EpistemicAxiomState(CoreasonBaseState):
    source_concept_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="CID of the origin node."
    )
    directed_edge_type: OBORelationEdge = Field(description="The topological relationship.")
    target_concept_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="CID of destination node."
    )

    @model_validator(mode="after")
    def validate_domain_extensions(self, info: ValidationInfo) -> Self:
        allowed_exts = (info.context or {}).get("allowed_ext_intents", set())
        for k, v in self.__dict__.items():
            if isinstance(v, str) and v.startswith("ext:") and v not in allowed_exts:
                raise ValueError(f"Unauthorized extension string in field {k}: {v}")
            elif isinstance(v, dict):
                for dk, dv in v.items():
                    if isinstance(dk, str) and dk.startswith("ext:") and dk not in allowed_exts:
                        raise ValueError(f"Unauthorized extension string in dict key of {k}: {dk}")
                    if isinstance(dv, str) and dv.startswith("ext:") and dv not in allowed_exts:
                        raise ValueError(f"Unauthorized extension string in dict value of {k}: {dv}")
        return self"""

if axiom_old in content:
    content = content.replace(axiom_old, axiom_new)
    print("Patched EpistemicAxiomState")
else:
    print("EpistemicAxiomState not found!")

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
