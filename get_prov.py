with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "class EpistemicProvenanceReceipt(CoreasonBaseState):" in line:
        for j in range(i, i+30):
            print(lines[j], end='')
        break
