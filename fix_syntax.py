with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

content = content.replace("except ValueError, TypeError:", "except (ValueError, TypeError):")

with open('src/coreason_manifest/spec/ontology.py', 'w') as f:
    f.write(content)
