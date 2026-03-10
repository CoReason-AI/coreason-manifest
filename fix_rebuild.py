with open("src/coreason_manifest/spec/ontology.py") as f:
    c = f.read()

# Add the rebuilds at the end.
rebuild_code = """
# Stratum 9 Resolvers
BaseTopology.model_rebuild()
DAGTopology.model_rebuild()
CouncilTopology.model_rebuild()
SwarmTopology.model_rebuild()
EvolutionaryTopology.model_rebuild()
SMPCTopology.model_rebuild()
EvaluatorOptimizerTopology.model_rebuild()
DigitalTwinTopology.model_rebuild()
AdversarialMarketTopology.model_rebuild()
ConsensusFederationTopology.model_rebuild()
"""

if "BaseTopology.model_rebuild()" not in c:
    with open("src/coreason_manifest/spec/ontology.py", "a") as f:
        f.write("\n" + rebuild_code)
