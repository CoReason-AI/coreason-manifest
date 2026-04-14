# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import re

ONTOLOGY = "src/coreason_manifest/spec/ontology.py"

with open(ONTOLOGY, encoding="utf-8") as f:
    content = f.read()

# ============================================================
# ACTION 1: Delete fragmented logic classes
# ============================================================

# Delete all 6 classes (from class definition to the next class or function)
classes_to_delete = [
    "EpistemicLean4Premise",
    "Lean4VerificationReceipt",
    "EpistemicLogicPremise",
    "FormalLogicProofReceipt",
    "EpistemicPrologPremise",
    "PrologDeductionReceipt",
]

for cls_name in classes_to_delete:
    # Match from "class ClassName(...)" to the next "\nclass " or "\ndef " or "\ntype "
    pattern = rf"\nclass {cls_name}\(CoreasonBaseState\):.*?(?=\nclass |\ndef |\ntype )"
    match = re.search(pattern, content, flags=re.DOTALL)
    if match:
        content = content[: match.start()] + "\n" + content[match.end() :]
        print(f"  Deleted class: {cls_name}")
    else:
        print(f"  WARNING: Could not find class: {cls_name}")

# Delete 3 MCP tool generator functions
for func_name in ["generate_lean4_mcp_tool", "generate_clingo_mcp_tool", "generate_prolog_mcp_tool"]:
    pattern = rf"\ndef {func_name}\(\).*?(?=\ndef |\ntype |\nclass )"
    match = re.search(pattern, content, flags=re.DOTALL)
    if match:
        content = content[: match.start()] + "\n" + content[match.end() :]
        print(f"  Deleted function: {func_name}")
    else:
        print(f"  WARNING: Could not find function: {func_name}")

# ============================================================
# ACTION 2: Inject unified categorical abstractions
# ============================================================

# Insert before DocumentKnowledgeGraphManifest
UNIFIED_CLASSES = '''
class FormalLogicPremise(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A unified categorical abstraction for all formal logic, constraint satisfaction, and theorem-proving hypotheses.

    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to model and solve logic domains by mapping the declarative payload to the target solver defined by the dialect_urn.

    EPISTEMIC BOUNDS: Constrained strictly to formal syntaxes (e.g., SMT-LIB, Lean 4, ASP, Prolog) via high-capacity string bounds.

    MCP ROUTING TRIGGERS: Automated Theorem Proving, Constraint Satisfaction, Logic Programming, Substrate Oracle
    """

    topology_class: Literal["formal_logic_premise"] = Field(default="formal_logic_premise")
    dialect_urn: Annotated[str, StringConstraints(pattern=r"^urn:coreason:.*$")] = Field(
        description="The URN identifying the specific formal dialect or solver (e.g., 'urn:coreason:dialect:lean4', 'urn:coreason:dialect:clingo')."
    )
    formal_statement: Annotated[str, StringConstraints(max_length=100000)] = Field(
        description="The primary logical query, theorem, or ASP program."
    )
    verification_script: Annotated[str, StringConstraints(max_length=100000)] | None = Field(
        default=None,
        description="Optional auxiliary scripts required for verification, such as Lean 4 tactic proofs or Prolog ephemeral facts.",
    )


class FormalVerificationReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A cryptographically frozen historical fact representing the unified outcome of a formal logic evaluation or theorem proof.

    CAUSAL AFFORDANCE: Unlocks System 2 remediation loops or graph progression by providing deterministic, algebraically verified execution traces and truth values.

    EPISTEMIC BOUNDS: Cryptographically anchored to the Merkle-DAG. The boolean 'is_proved' definitively represents mathematical truth.

    MCP ROUTING TRIGGERS: System 2 Remediation, Mathematical Truth, Proof Verification, Epistemic Ledger
    """

    event_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")] = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the Merkle-DAG."
    )
    prior_event_hash: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-f0-9]{64}$")] | None = Field(
        default=None, description="The RFC 8785 Canonical hash of the immediate causal ancestor."
    )
    timestamp: float = Field(ge=0.0, description="The precise temporal coordinate of the event realization.")

    topology_class: Literal["formal_verification_receipt"] = Field(default="formal_verification_receipt")
    causal_provenance_id: NodeCIDState | None = Field(
        default=None, description="Pointer to the specific node or intent that requested this formal verification."
    )
    is_proved: bool = Field(
        description="The definitive Boolean evaluating whether the proof succeeded, the program is satisfiable, or the deduction holds true."
    )
    satisfiability_state: Literal["SATISFIABLE", "UNSATISFIABLE", "UNKNOWN", "OPTIMUM FOUND"] | None = Field(
        default=None, description="Detailed satisfiability state, primarily utilized by ASP/SMT solvers."
    )
    failing_context: Annotated[str, StringConstraints(max_length=100000)] | None = Field(
        default=None,
        description="The specific failing tactic state, counter-model, or syntax error preventing verification.",
    )
    extracted_bindings: list[dict[Annotated[str, StringConstraints(max_length=255)], JsonPrimitiveState]] = Field(
        default_factory=list,
        json_schema_extra={"coreason_topological_exemption": True},
        description="Topological Exemption: DO NOT SORT. Captures answer sets or unification bindings extracted by the oracle.",
    )

    @field_serializer("extracted_bindings")
    def serialize_extracted_bindings(
        self, bindings: list[dict[str, JsonPrimitiveState]], _info: Any
    ) -> list[dict[str, JsonPrimitiveState]]:
        # Topological Exemption: Freeze the outer list sequence (the mathematical order of unification/answer sets).
        # However, to maintain RFC 8785 compliance, sort the keys *inside* the individual dictionaries.
        return [dict(sorted(b.items())) for b in bindings]


'''

content = content.replace(
    "class DocumentKnowledgeGraphManifest(CoreasonBaseState):",
    UNIFIED_CLASSES + "class DocumentKnowledgeGraphManifest(CoreasonBaseState):",
)
print("  Injected FormalLogicPremise and FormalVerificationReceipt")

# ============================================================
# ACTION 3: Update Discriminated Unions
# ============================================================

# AnyIntent: remove old, add new
content = content.replace(
    "    | EpistemicLean4Premise\n    | EpistemicLogicPremise\n    | EpistemicPrologPremise\n",
    "    | FormalLogicPremise\n",
)
print("  Updated AnyIntent union")

# AnyStateEvent: remove old, add new
content = content.replace(
    "    | Lean4VerificationReceipt\n    | FormalLogicProofReceipt\n    | PrologDeductionReceipt\n",
    "    | FormalVerificationReceipt\n",
)
print("  Updated AnyStateEvent union")

# ============================================================
# ACTION 4: Update documentation references
# ============================================================

content = content.replace(
    '"MUST point to a FormalLogicProofReceipt evaluating to SATISFIABLE to collapse the hypothesis."',
    '"MUST point to a FormalVerificationReceipt evaluating to SATISFIABLE to collapse the hypothesis."',
)
content = content.replace(
    '"Pointer to a Lean4VerificationReceipt or HoareLogicProofReceipt validating the logic."',
    '"Pointer to a FormalVerificationReceipt or HoareLogicProofReceipt validating the logic."',
)
content = content.replace(
    '"If grounding via strict hierarchies (e.g., medical ontologies), this MUST point to a PrologDeductionReceipt with truth_value=True."',
    '"If grounding via strict hierarchies (e.g., medical ontologies), this MUST point to a FormalVerificationReceipt with is_proved=True."',
)
print("  Updated documentation references")

# ============================================================
# ACTION 5: Update model_rebuild() footers
# ============================================================

old_rebuilds = """EpistemicLean4Premise.model_rebuild()
Lean4VerificationReceipt.model_rebuild()
EpistemicLogicPremise.model_rebuild()
FormalLogicProofReceipt.model_rebuild()
EpistemicPrologPremise.model_rebuild()
PrologDeductionReceipt.model_rebuild()"""

new_rebuilds = """FormalLogicPremise.model_rebuild()
FormalVerificationReceipt.model_rebuild()"""

content = content.replace(old_rebuilds, new_rebuilds)
print("  Updated model_rebuild() calls")

with open(ONTOLOGY, "w", encoding="utf-8") as f:
    f.write(content)

print("\nEpic 3 ontology refactoring complete!")
