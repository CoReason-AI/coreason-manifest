with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

import re

# We need to insert DomainExtensionString type near the top.
# `type JsonPrimitiveState` is a good place to insert before.
target = "type JsonPrimitiveState ="

if target in content:
    insertion = """# The Extension Namespace Boundary
type DomainExtensionString = Annotated[
    str,
    StringConstraints(pattern="^ext:[a-zA-Z0-9_.-]+$", max_length=128)
]

"""
    new_content = content.replace(target, insertion + target)
    with open("src/coreason_manifest/spec/ontology.py", "w") as f:
        f.write(new_content)
    print("Success")
else:
    print("Target not found")
