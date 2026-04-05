with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith("type NodeIdentifierState =") or \
       line.startswith("type ProfileIdentifierState =") or \
       line.startswith("type ToolIdentifierState =") or \
       line.startswith("type TopologyHashReceipt ="):
        print(f"--- {line.split(' ')[1]} ---")
        j = i
        while j < len(lines) and not lines[j].strip().endswith("]"):
            print(lines[j], end='')
            j += 1
        print(lines[j], end='')
