import re

missing = [
    ('AnalogicalMappingTask', 'analogical_mapping_task'),
    ('BoundedJSONRPCIntent', 'bounded_json_rpc_intent'),
    ('ChaosExperimentTask', 'chaos_experiment_task'),
    ('EpistemicTransmutationTask', 'epistemic_transmutation_task'),
    ('EpistemicUpsamplingTask', 'epistemic_upsampling_task'),
    ('InterventionalCausalTask', 'interventional_causal_task'),
    ('MCPClientIntent', 'mcp_client_intent'),
    ('RollbackIntent', 'rollback_intent'),
    ('StateMutationIntent', 'state_mutation_intent'),
]

with open('src/coreason_manifest/spec/ontology.py', 'r', encoding='utf-8') as f:
    content = f.read()

for cls, sn in missing:
    if f'topology_class: Literal["{sn}"]' in content:
        continue
    # Insert right after `class {cls}(CoreasonBaseState):`
    # or `class {cls}(...):`
    pattern = re.compile(f'(class {cls}\\([^)]+\\):\\n)', re.DOTALL)
    replacement = f'\\g<1>    topology_class: Literal["{sn}"] = Field(default="{sn}")\\n'
    content = pattern.sub(replacement, content, count=1)

# Now also append to AnyIntent!
def replace_any_intent(c):
    start = c.find('type AnyIntent = Annotated[')
    if start == -1: return c
    end = c.find(']', start)
    block = c[start:end]
    
    # Check if we already appended
    if 'AnalogicalMappingTask' in block:
        return c
        
    s = block.replace('    | SPARQLQueryIntent,', '    | SPARQLQueryIntent\n    | AnalogicalMappingTask\n    | BoundedJSONRPCIntent\n    | ChaosExperimentTask\n    | EpistemicTransmutationTask\n    | EpistemicUpsamplingTask\n    | InterventionalCausalTask\n    | MCPClientIntent\n    | RollbackIntent\n    | StateMutationIntent,')
    return c[:start] + s + c[end:]

content = replace_any_intent(content)

with open('src/coreason_manifest/spec/ontology.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Injected discriminators and added to AnyIntent safely.')
