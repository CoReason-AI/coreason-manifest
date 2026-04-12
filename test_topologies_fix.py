with open('tests/fuzzing/test_topologies.py', 'r') as f:
    content = f.read()

# Let's search and replace with regex more safely
import re

content = re.sub(
    r'CausalDirectedEdgeState\([^)]+\)',
    'CausalDirectedEdgeState(source_variable="A", target_variable="B", edge_class="direct_cause", predicate_curie="test:pred", grounding_sla=EvidentiaryGroundingSLA(minimum_nli_entailment_score=0.5, require_independent_sources=1, ungrounded_link_action="sever_edge", allowed_evidence_domains=["test"]))',
    content
)

with open('tests/fuzzing/test_topologies.py', 'w') as f:
    f.write(content)
