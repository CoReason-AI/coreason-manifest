import sys
from pathlib import Path
import re

spec_init = Path('src/coreason_manifest/spec/__init__.py').read_text(encoding='utf-8')
match = re.search(r'__all__ = \[\n(.*?)\]', spec_init, re.DOTALL)
all_items = [x.strip().strip('"').strip("'") for x in match.group(1).split(',')] if match else []

ontology = Path('src/coreason_manifest/spec/ontology.py').read_text(encoding='utf-8')
type_aliases = []
for line in ontology.splitlines():
    if line.startswith('type '):
        m = re.search(r'^type ([A-Za-z0-9_]+)', line)
        if m:
            type_aliases.append(m.group(1))

# Intersection
to_import = sorted([t for t in type_aliases if t in all_items])
print('\n    '.join(to_import))
