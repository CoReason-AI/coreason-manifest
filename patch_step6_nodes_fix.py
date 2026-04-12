with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()

import re

# Move the validator down for SemanticEdgeState
bad_order = """class SemanticEdgeState(CoreasonBaseState):
    @model_validator(mode="after")
    def enforce_evidence_or_sla(self) -> Self:
        if self.belief_vector is None and self.grounding_sla is None:
            raise ValueError("Edge must possess either empirical evidence (belief_vector) or an explicit grounding_sla.")
        return self"""

content = content.replace(bad_order, "class SemanticEdgeState(CoreasonBaseState):")

# Find the end of SemanticEdgeState to insert it properly.
match = re.search(r"(class SemanticEdgeState.*?)(?=\n\nclass|\n\n\w)", content, re.DOTALL)
if match:
    cls_body = match.group(1)
    new_cls_body = (
        cls_body
        + """

    @model_validator(mode="after")
    def enforce_evidence_or_sla(self) -> Self:
        if self.belief_vector is None and self.grounding_sla is None:
            raise ValueError("Edge must possess either empirical evidence (belief_vector) or an explicit grounding_sla.")
        return self"""
    )
    content = content.replace(cls_body, new_cls_body)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
