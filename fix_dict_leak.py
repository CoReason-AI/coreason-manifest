
with open("src/coreason_manifest/spec/ontology.py") as f:
    lines = f.readlines()

# The script errantly added le= to some lists and dicts.
# Let's just remove le=... from fields that are clearly dict/list.
for i, line in enumerate(lines):
    if "le=1000000000" in line or "le=1000000000.0" in line:
        # We need to see what the type hint was.
        # But we can just use `git show HEAD:src/coreason_manifest/spec/ontology.py > old.py` and see what was missing.
        pass
