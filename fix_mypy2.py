import re

with open("tests/contracts/test_ontology_payload_bounds.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "source_entity=" in line and "Amoxicillin" in line:
        lines[i] = '            source_entity="Amoxicillin 500mg",  # type: ignore\n'

with open("tests/contracts/test_ontology_payload_bounds.py", "w") as f:
    f.writelines(lines)
