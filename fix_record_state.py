with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

import re

# We need to add event_cid, timestamp, prior_event_hash to SemanticRelationalRecordState
old_str = """
class SemanticRelationalRecordState(CoreasonBaseState):
    \"\"\"AGENT INSTRUCTION: Represents the untyped payload injection zone for harmonized structured telemetry. CAUSAL AFFORDANCE: Permits specialized downstream agents to project and decode specific industry payloads (e.g., OMOP CDM, FIX protocol) while preserving universal mathematical traversal of the graph. EPISTEMIC BOUNDS: The payload_injection_zone is routed through the volumetric hardware guillotine.\"\"\"

    topology_class: Literal["semantic_relational_record"] = Field(default="semantic_relational_record")
    record_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")] = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this record."
    )
"""

new_str = """
class SemanticRelationalRecordState(CoreasonBaseState):
    \"\"\"AGENT INSTRUCTION: Represents the untyped payload injection zone for harmonized structured telemetry. CAUSAL AFFORDANCE: Permits specialized downstream agents to project and decode specific industry payloads (e.g., OMOP CDM, FIX protocol) while preserving universal mathematical traversal of the graph. EPISTEMIC BOUNDS: The payload_injection_zone is routed through the volumetric hardware guillotine.\"\"\"

    topology_class: Literal["semantic_relational_record"] = Field(default="semantic_relational_record")
    event_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")] = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the Merkle-DAG.",
    )
    prior_event_hash: (
        Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-f0-9]{64}$")] | None
    ) = Field(
        default=None,
        description="The RFC 8785 Canonical hash of the immediate causal ancestor, securing the Merkle-DAG.",
    )
    timestamp: float = Field(description="The precise temporal coordinate of the event realization.")
    record_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")] = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this record."
    )
"""

content = content.replace(old_str, new_str)
with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
