import re

with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

# Insert ManifestViolationReceipt before System2RemediationIntent
new_class = """
class ManifestViolationReceipt(CoreasonBaseState):
    \"\"\"
    AGENT INSTRUCTION: A machine-readable, deterministic JSON receipt of an exact topological failure, replacing unstructured stack traces.

    CAUSAL AFFORDANCE: Enables the agent to execute $O(1)$ surgical patches via StateMutationIntent rather than hallucinating fixes.

    EPISTEMIC BOUNDS: failing_pointer maps exactly to RFC 6902 JSON Pointers.

    MCP ROUTING TRIGGERS: Fault Receipt, RFC 6902, Epistemic Loss Prevention
    \"\"\"

    failing_pointer: str = Field(max_length=2000, description="The exact RFC 6902 JSON pointer isolating the topological failure.")
    violation_type: str = Field(max_length=255, description="Categorical descriptor of the failure, e.g., missing, type_error.")
    diagnostic_message: str = Field(max_length=2000, description="The specific constraint breached.")

"""

content = content.replace("class System2RemediationIntent(CoreasonBaseState):", new_class + "class System2RemediationIntent(CoreasonBaseState):")

# Update System2RemediationIntent
search = """    failing_pointers: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        min_length=1,
        description="A strictly typed array of RFC 6902 JSON Pointers isolating the exact topological coordinate of the hallucination.",
    )
    remediation_prompt: Annotated[str, StringConstraints(max_length=100000)] = Field(
        min_length=1, description="The deterministic, non-monotonic natural-language constraint the agent must satisfy."
    )

    @model_validator(mode="after")
    def _enforce_canonical_sort_failing_pointers(self) -> Self:
        \"\"\"Mathematically sort pointers to guarantee deterministic canonical hashing.\"\"\"
        object.__setattr__(self, "failing_pointers", sorted(self.failing_pointers))
        return self"""

replace = """    violation_receipts: list[ManifestViolationReceipt] = Field(
        min_length=1,
        description="The deterministic array of exact structural faults the agent must correct."
    )

    @model_validator(mode="after")
    def _enforce_canonical_sort_receipts(self) -> Self:
        \"\"\"Mathematically sort receipts to guarantee deterministic canonical hashing.\"\"\"
        object.__setattr__(self, "violation_receipts", sorted(self.violation_receipts, key=lambda x: x.failing_pointer))
        return self"""

content = content.replace(search, replace)

content += "\nManifestViolationReceipt.model_rebuild()\nSystem2RemediationIntent.model_rebuild()\n"

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
