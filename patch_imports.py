with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

# Make sure ValidationInfo is imported
if "ValidationInfo" not in content:
    content = content.replace(
        "from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, field_validator, model_validator",
        "from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, ValidationInfo, field_validator, model_validator"
    )

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)

print("Imports updated")
