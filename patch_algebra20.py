import re

with open("tests/contracts/test_algebra_hypothesis.py", "r") as f:
    content = f.read()

# TamperFaultEvent import was actually placed on another line
content = content.replace("from coreason_manifest.spec.ontology import (\n    OntologicalAlignmentPolicy,", "from coreason_manifest.spec.ontology import (\n    OntologicalAlignmentPolicy, TamperFaultEvent,")

with open("tests/contracts/test_algebra_hypothesis.py", "w") as f:
    f.write(content)
