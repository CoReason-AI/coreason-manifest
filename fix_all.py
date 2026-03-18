import re

with open("tests/contracts/test_ontology_hypothesis.py", "r") as f:
    content = f.read()

# fix test_utility_justification_graph_receipt_interlock
content = content.replace('ensemble = EnsembleTopologyProfile(nodes={}, routing_strategy="majority_vote", concurrent_branch_ids=["1"], fusion_function="test")', 'ensemble = EnsembleTopologyProfile(nodes={}, routing_strategy="majority_vote", concurrent_branch_ids=["1234567"], fusion_function="weighted_consensus")')

# fix test_agent_node_profile_sorting
content = re.sub(r'VerifiableCredentialPresentationReceipt\(\s*presentation_format="jwt_vc",\s*issuer_did=i if len\(i\) >= 7 else i\.ljust\(7, "0"\),\s*cryptographic_proof_blob="b"\*64,\s*authorization_claims=\{"claim": "value"\}\s*\)', 'VerifiableCredentialPresentationReceipt(presentation_format="jwt_vc", issuer_did="did:example:" + i.replace(":", ""), cryptographic_proof_blob="b"*64, authorization_claims={"claim": "value"})', content)

# fix StructuralCausalModelManifest missing import
content = content.replace('from coreason_manifest.spec.ontology import StructuralCausalModelManifest, CausalDirectedEdgeState', 'from coreason_manifest.spec.ontology import CausalDirectedEdgeState\n    from coreason_manifest.spec.ontology import StructuralCausalModelManifest')

# fix test_theory_of_mind_snapshot_sorting missing import
content = content.replace('from coreason_manifest.spec.ontology import AgentMemorySnapshot, TheoryOfMindSnapshot, SemanticCapabilityAttestationReceipt', 'from coreason_manifest.spec.ontology import AgentMemorySnapshot, TheoryOfMindSnapshot, SemanticCapabilityAttestationReceipt\n    from coreason_manifest.spec.ontology import AgentMemorySnapshot')

with open("tests/contracts/test_ontology_hypothesis.py", "w") as f:
    f.write(content)
