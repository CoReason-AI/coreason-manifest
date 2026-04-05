with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    lines = f.readlines()

in_class = False
for line in lines:
    if line.startswith("class AgentNodeProfile(CoreasonBaseState):"):
        in_class = True
    if in_class:
        if line.startswith("    @model_validator"):
            print(line, end='')
            continue
        if line.startswith("    def _enforce"):
            print(line, end='')
            continue
        if "object.__setattr__" in line:
            print(line, end='')
            continue
        if "return self" in line:
            print(line, end='')
            continue
        if line.startswith("class ") and not line.startswith("class AgentNodeProfile"):
            break
