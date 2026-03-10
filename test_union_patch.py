
filepath = "src/coreason_manifest/spec/ontology.py"
with open(filepath) as f:
    content = f.read()

# Let's search if AnyNode/AnyTopology mapping patch is needed
if "AnyNode" in content or "mapping" in content:
    print("Found mapping or AnyNode")
else:
    print("Not found")
