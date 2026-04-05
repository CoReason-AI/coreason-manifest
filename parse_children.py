import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

for base in ['BaseStateEvent', 'BaseNodeProfile', 'BaseTopologyManifest', 'BaseIntent']:
    pattern = r'class ([A-Za-z0-9_]+)\((.*?)\):'
    for match in re.finditer(pattern, content):
        name, bases = match.groups()
        bases_list = [b.strip() for b in bases.split(',')]
        if base in bases_list:
            print(f"{name} inherits from {base}")
