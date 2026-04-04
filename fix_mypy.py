with open("tests/contracts/test_ontology_payload_bounds.py", "r") as f:
    content = f.read()

content = content.replace(
    'source_entity="Amoxicillin 500mg", # type: ignore',
    'source_entity="Amoxicillin 500mg",  # type: ignore[arg-type]'
)
with open("tests/contracts/test_ontology_payload_bounds.py", "w") as f:
    f.write(content)
