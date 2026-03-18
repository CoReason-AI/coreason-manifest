import re

with open("tests/contracts/test_ontology_hypothesis.py", "r") as f:
    content = f.read()

# I see it should be AgentWorkingMemorySnapshot instead of AgentWorkingMemoryProfile, let's fix
content = content.replace("AgentWorkingMemoryProfile", "AgentWorkingMemorySnapshot")

# And for CausalDirectedEdgeState, there are no node ids
content = content.replace("assert manifest.causal_edges == sorted(edges, key=lambda x: (getattr(x, 'source_node_id', None), getattr(x, 'target_node_id', None)))", "assert manifest.causal_edges == sorted(edges, key=lambda x: (x.source_variable, x.target_variable))")

with open("tests/contracts/test_ontology_hypothesis.py", "w") as f:
    f.write(content)
