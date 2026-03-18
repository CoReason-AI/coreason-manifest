import re

with open("tests/contracts/test_algebra_hypothesis.py", "r") as f:
    content = f.read()

content = content.replace("from coreason_manifest.spec.ontology import TamperFaultEvent, \n    EpistemicLedgerState,", "from coreason_manifest.spec.ontology import (\n    TamperFaultEvent,\n    EpistemicLedgerState,")

with open("tests/contracts/test_algebra_hypothesis.py", "w") as f:
    f.write(content)
