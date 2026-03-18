import re

with open("tests/contracts/test_algebra_hypothesis.py", "r") as f:
    content = f.read()

# Fix syntax error from previous replace
content = content.replace("from coreason_manifest.spec.ontology import (\n    OntologicalAlignmentPolicy, TamperFaultEvent,", "from coreason_manifest.spec.ontology import (\n    OntologicalAlignmentPolicy,\n    TamperFaultEvent,")

with open("tests/contracts/test_algebra_hypothesis.py", "w") as f:
    f.write(content)
