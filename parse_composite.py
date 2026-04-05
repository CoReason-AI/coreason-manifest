with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    lines = f.readlines()

in_class = False
for line in lines:
    if line.startswith("class CompositeNodeProfile(CoreasonBaseState):"):
        in_class = True
    if in_class:
        print(line, end='')
        if line.startswith("class "):
            pass # ignore first
        elif line.startswith("class ") or line.startswith("type "):
            break
