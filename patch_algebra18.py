import re

with open("tests/contracts/test_algebra_hypothesis.py", "r") as f:
    content = f.read()

# Fix `test_calculate_latent_alignment` exception check.
content = content.replace('from coreason_manifest.spec.ontology import OntologicalAlignmentPolicy, VectorEmbeddingState', 'from coreason_manifest.spec.ontology import OntologicalAlignmentPolicy, VectorEmbeddingState, TamperFaultEvent')

with open("tests/contracts/test_algebra_hypothesis.py", "w") as f:
    f.write(content)
