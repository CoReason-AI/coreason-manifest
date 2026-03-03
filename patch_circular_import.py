with open("src/coreason_manifest/core/telemetry/telemetry_schemas.py", "r") as f:
    content = f.read()

content = content.replace("from coreason_manifest.core.workflow import LineageIntegrityError", "from coreason_manifest.core.workflow.exceptions import LineageIntegrityError")

with open("src/coreason_manifest/core/telemetry/telemetry_schemas.py", "w") as f:
    f.write(content)
