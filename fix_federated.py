with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()

print("FederatedSecurityMacroManifest" in content)
