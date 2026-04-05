import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    lines = f.readlines()

aliases = ['NodeIdentifierState', 'ProfileIdentifierState', 'ToolIdentifierState', 'TopologyHashReceipt']
for alias in aliases:
    for line in lines:
        if line.startswith(f"type {alias} ="):
            print(line.strip())
