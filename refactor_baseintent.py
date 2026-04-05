import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

pattern = r'class FYIIntent\(BaseIntent\):'
content = re.sub(pattern, 'class FYIIntent(CoreasonBaseState):', content)

# Remove BaseIntent definition completely
base_pattern = r'class BaseIntent\(CoreasonBaseState\):\s*(?:r?"""[\s\S]*?"""|r?\'\'\'[\s\S]*?\'\'\')?\s*\n'
content = re.sub(base_pattern, '', content)

with open('src/coreason_manifest/spec/ontology.py', 'w') as f:
    f.write(content)
