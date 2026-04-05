import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

# Add a sorting `@model_validator` to `EpistemicChainGraphState` to physically sort its `syntactic_roots` array
# `object.__setattr__(self, "syntactic_roots", sorted(self.syntactic_roots))`
pattern = r'class EpistemicChainGraphState\(CoreasonBaseState\):[\s\S]*?def _enforce_canonical_sort\(self\) -> Self:'

def repl(m):
    return m.group(0).replace('def _enforce_canonical_sort(self) -> Self:', 'def _enforce_canonical_sort(self) -> Self:\n        object.__setattr__(self, "syntactic_roots", sorted(self.syntactic_roots))')

content = re.sub(pattern, repl, content)

with open('src/coreason_manifest/spec/ontology.py', 'w') as f:
    f.write(content)
