with open("src/coreason_manifest/spec/ontology.py") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith("type TelemetryScalarState = str | int | float | bool | None"):
        lines[i] = (
            "type TelemetryScalarState = Annotated[str, StringConstraints(max_length=100000)] | int | float | bool | None\n"
        )

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.writelines(lines)
