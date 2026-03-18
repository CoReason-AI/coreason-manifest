from coreason_manifest.spec.ontology import CausalDirectedEdgeState, StructuralCausalGraphProfile, AgentNodeProfile, TheoryOfMindSnapshot, AgentWorkingMemoryProfile, AbductiveHypothesis

print(CausalDirectedEdgeState.model_fields.keys())

try:
    edge = CausalDirectedEdgeState(source_variable="a", target_variable="b", edge_type="direct_cause")
    print("edge created")
    print(getattr(edge, 'source_node_id', None))
except Exception as e:
    print(e)

print("AgentNodeProfile keys:")
print(AgentNodeProfile.model_fields.keys())

print("AbductiveHypothesis keys:")
print(AbductiveHypothesis.model_fields.keys())

print("AgentWorkingMemoryProfile keys:")
print(AgentWorkingMemoryProfile.model_fields.keys())
