from coreason_manifest.spec.ontology import StructuralCausalGraphProfile, CausalDirectedEdgeState
try:
    edge1 = CausalDirectedEdgeState(source_variable="b", target_variable="a", edge_type="direct_cause")
    edge2 = CausalDirectedEdgeState(source_variable="a", target_variable="b", edge_type="direct_cause")
    profile = StructuralCausalGraphProfile(observed_variables=["a", "b"], latent_variables=[], causal_edges=[edge1, edge2])
    print(profile)
except Exception as e:
    print(e)
