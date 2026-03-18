import re

with open("tests/contracts/test_ontology_hypothesis.py", "r") as f:
    content = f.read()

# fix test_agent_node_profile_sorting to generate valid dids
content = re.sub(
    r'VerifiableCredentialPresentationReceipt\(presentation_format="jwt_vc", issuer_did=i if len\(i\) >= 7 else i\.ljust\(7, "0"\), cryptographic_proof_blob="b"\*64, authorization_claims=\{"claim": "value"\}\)',
    'VerifiableCredentialPresentationReceipt(presentation_format="jwt_vc", issuer_did="did:example:" + re.sub(r"[^a-zA-Z0-9.-_:]", "", i)[:50] + "1", cryptographic_proof_blob="b"*64, authorization_claims={"claim": "value"})',
    content
)

# find correct class names
content = content.replace("StructuralCausalModelManifest", "PearlCausalModelManifest")
content = content.replace("AgentMemorySnapshot", "AgentWorkingMemoryProfile") # actually what is it? I will check
content = content.replace("AgentWorkingMemorySnapshot", "AgentWorkingMemoryProfile")

with open("tests/contracts/test_ontology_hypothesis.py", "w") as f:
    f.write(content)
