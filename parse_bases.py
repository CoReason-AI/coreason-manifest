import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    lines = f.readlines()

def print_class(name):
    for i, line in enumerate(lines):
        if line.startswith(f'class {name}('):
            print(f"--- {name} at line {i+1} ---")
            j = i
            while j < len(lines):
                print(lines[j], end='')
                j += 1
                if j < len(lines) and lines[j].startswith('class '):
                    break

print_class('BaseStateEvent')
print_class('BaseNodeProfile')
print_class('BaseTopologyManifest')
print_class('BaseIntent')
