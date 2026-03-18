with open("tests/contracts/test_ontology_hypothesis.py", "r") as f:
    content = f.read()

content = content.replace(
    'ensemble = EnsembleTopologyProfile(nodes={}, routing_strategy="majority_vote", concurrent_branch_ids=["1234567"], fusion_function="weighted_consensus")',
    'ensemble = EnsembleTopologyProfile(concurrent_branch_ids=["did:example:1234567", "did:example:7654321"], fusion_function="weighted_consensus")'
)

with open("tests/contracts/test_ontology_hypothesis.py", "w") as f:
    f.write(content)
