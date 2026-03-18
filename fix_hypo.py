with open("tests/contracts/test_ontology_hypothesis.py", "r") as f:
    content = f.read()

content = content.replace("CausalHypothesisState", "SteadyStateHypothesisState")
content = content.replace("from coreason_manifest.spec.ontology import SteadyStateHypothesisState, FalsificationContract", "from coreason_manifest.spec.ontology import SteadyStateHypothesisState, FalsificationContract")

with open("tests/contracts/test_ontology_hypothesis.py", "w") as f:
    f.write(content)
