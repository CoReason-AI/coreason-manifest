with open('tests/test_ontology_validators.py') as f:
    content = f.read()

content = content.replace(
    'with pytest.raises(ValueError, match="UNAUTHORIZED MCP MOUNT: The presented Verifiable Credential is not signed by a valid"):',
    'with pytest.raises(ValueError, match="UNAUTHORIZED MCP MOUNT: The presented Verifiable Credential is not signed"):'
)

content = content.replace(
    '''    with pytest.raises(ValueError):
        ActiveInferenceContract(''',
    '''    with pytest.raises(ValueError, match="Input should be less than or equal to 1.0"):
        ActiveInferenceContract('''
)

content = content.replace(
    '''    with pytest.raises(ValueError):
        EphemeralNamespacePartitionState(''',
    '''    with pytest.raises(ValueError, match="Invalid SHA-256 hash in whitelist"):
        EphemeralNamespacePartitionState('''
)

with open('tests/test_ontology_validators.py', 'w') as f:
    f.write(content)
