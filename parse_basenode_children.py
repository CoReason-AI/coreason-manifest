import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

pattern = r'class ([A-Za-z0-9_]+)\(BaseNodeProfile\):'
matches = re.findall(pattern, content)
print("Children of BaseNodeProfile:", matches)
