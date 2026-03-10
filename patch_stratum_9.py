with open("src/coreason_manifest/spec/ontology.py") as f:
    c = f.read()

# Find the end where the rebuilds are and replace them
# Let's just find CompositeNode.model_rebuild() and replace everything after it.
idx = c.find("CompositeNode.model_rebuild()")
if idx != -1:
    c = c[:idx]

rebuild_block = """# =========================================================================
# STRATUM 9: TOPOLOGICAL RESOLUTION (FORWARD REF EVALUATION)
# =========================================================================

CompositeNode.model_rebuild()
WorkflowEnvelope.model_rebuild()
MCPServerConfig.model_rebuild()

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

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c.rstrip() + "\n\n" + rebuild_block)
